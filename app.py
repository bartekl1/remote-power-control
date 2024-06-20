from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import paramiko.dsskey
import paramiko.ecdsakey
import paramiko.ed25519key
import paramiko.rsakey
from wakeonlan import send_magic_packet
import paramiko
import mysql.connector
import pyotp

import json
import random
import time
import string
import hashlib
import io

with open("configs.json") as file:
    configs = json.load(file)

    mysql_configs = {}
    if "mysql_host" in configs.keys():
        mysql_configs["host"] = configs["mysql_host"]
    if "mysql_port" in configs.keys():
        mysql_configs["port"] = configs["mysql_port"]
    if "mysql_user" in configs.keys():
        mysql_configs["user"] = configs["mysql_user"]
    if "mysql_password" in configs.keys():
        mysql_configs["password"] = configs["mysql_password"]
    if "mysql_database" in configs.keys():
        mysql_configs["database"] = configs["mysql_database"]

login_manager = LoginManager()
app = Flask(__name__)
app.secret_key = configs["secret_key"]
login_manager.init_app(app)


class UserError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeviceError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class User(UserMixin):
    def __init__(self, user_id):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        if len(result) == 0:
            raise UserError("User not found")

        self.user_id: int = result[0]["id"]
        self.alternative_id: str = result[0]["alternative_id"]
        self.username: str = result[0]["username"]
        self.password_hash: str = result[0]["password_hash"]
        self.email: str = result[0]["email"]
        self.totp_secret: str = result[0]["totp_secret"]

    def get_id(self):
        return self.alternative_id

    @property
    def profile_picture_url(self):
        return f"https://gravatar.com/avatar/{hashlib.sha256(str(self.email).strip().lower().encode('utf-8')).hexdigest()}?s=200&d=mp"

    @property
    def enabled_2fa(self):
        return self.totp_secret is not None

    @property
    def url_2fa(self):
        if not self.enabled_2fa:
            return None
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(name=self.username, issuer_name="Remote Power Control")

    def check_password(self, password):
        ph = PasswordHasher()
        try:
            ph.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False
        else:
            if ph.check_needs_rehash(self.password_hash):
                self.change_password(password)
            return True

    def change_password(self, new_password):
        ph = PasswordHasher()

        self.alternative_id = "".join(random.choices(string.ascii_letters + string.digits, k=50)) + str(int(time.time() * 100))
        self.password_hash = ph.hash(new_password)

        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET alternative_id = %s, password_hash = %s WHERE id = %s", (self.alternative_id, self.password_hash, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def change_username(self, new_username):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET username = %s WHERE id = %s", (new_username, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def change_email(self, new_email):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def verify_otp(self, otp):
        if not self.enabled_2fa:
            return True
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(otp)

    def enable_2fa(self):
        self.totp_secret = pyotp.random_base32()

        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET totp_secret = %s WHERE id = %s", (self.totp_secret, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def disable_2fa(self):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET totp_secret = NULL WHERE id = %s", (self.user_id, ))

        db.commit()
        cursor.close()
        db.close()

    @staticmethod
    def get_by_username(username):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        if len(result) == 0:
            return None

        return User(result[0]["id"])

    @staticmethod
    def get_by_alternative_id(alternative_id):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE alternative_id = %s LIMIT 1", (alternative_id, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        if len(result) == 0:
            return None

        return User(result[0]["id"])

    @staticmethod
    def get_by_access_token(access_token):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM access_tokens WHERE token = %s LIMIT 1", (hashlib.sha256(access_token.encode('utf-8')).hexdigest(), ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        if len(result) == 0:
            return None

        return User(result[0]["user_id"])

    @property
    def devices(self):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM devices WHERE user_id = %s", (self.user_id, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        return [Device(row["id"]) for row in result]

    def create_device(self, name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command):
        return Device.create(self, name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command)

    @property
    def access_tokens(self):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM access_tokens WHERE user_id = %s", (self.user_id, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        return result

    def create_access_token(self, name):
        token = str(self.user_id) + str(int(time.time())) + "".join(random.choices(string.ascii_letters + string.digits, k=50))
        token = hashlib.sha256(token.encode('utf-8')).hexdigest()
        hashed_token = hashlib.sha256(token.encode('utf-8')).hexdigest()

        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("INSERT INTO access_tokens (user_id, name, token) VALUES (%s, %s, %s)", (self.user_id, name, hashed_token))
        db.commit()
        cursor.close()
        db.close()

        return token


class Device:
    def __init__(self, device_id):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM devices WHERE id = %s LIMIT 1", (device_id, ))
        result = cursor.fetchall()
        cursor.close()
        db.close()

        if len(result) == 0:
            raise DeviceError("Device not found")

        self.device_id: int = result[0]["id"]
        self.user_id: int = result[0]["user_id"]
        self.name: str = result[0]["name"]
        self.mac_address: str = result[0]["mac_address"]
        self.ip_address: str = result[0]["ip_address"]
        self.ssh_username: str = result[0]["ssh_username"]
        self.ssh_key_type: str = result[0]["ssh_key_type"]
        self.ssh_key: str = result[0]["ssh_key"]
        self.ssh_password: str = result[0]["ssh_password"]
        self.shutdown_command = result[0]["shutdown_command"]
        self.reboot_command = result[0]["reboot_command"]
        self.logout_command = result[0]["logout_command"]
        self.sleep_command = result[0]["sleep_command"]
        self.hibernate_command = result[0]["hibernate_command"]

    @property
    def user(self):
        return User(self.user_id)

    @property
    def wake_available(self):
        return self.mac_address is not None and self.mac_address != ""

    @property
    def shutdown_available(self):
        return self.ip_address is not None and self.ip_address != "" and self.shutdown_command is not None and self.shutdown_command != ""

    @property
    def reboot_available(self):
        return self.ip_address is not None and self.ip_address != "" and self.reboot_command is not None and self.reboot_command != ""

    @property
    def logout_available(self):
        return self.ip_address is not None and self.ip_address != "" and self.logout_command is not None and self.logout_command != ""

    @property
    def sleep_available(self):
        return self.ip_address is not None and self.ip_address != "" and self.sleep_command is not None and self.sleep_command != ""

    @property
    def hibernate_available(self):
        return self.ip_address is not None and self.ip_address != "" and self.hibernate_command is not None and self.hibernate_command != ""

    def wake(self):
        if not self.wake_available:
            raise DeviceError("Wake is not available for this device")
        send_magic_packet(self.mac_address)

    def _exec_ssh_command(self, command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.ssh_key is None or self.ssh_key == "":
            client.connect(hostname=self.ip_address,
                           username=self.ssh_username,
                           password=self.ssh_password,
                           allow_agent=False,
                           look_for_keys=False)
        else:
            if self.ssh_key_type == "DSA":
                key_class = paramiko.dsskey.DSSKey
            elif self.ssh_key_type == "RSA":
                key_class = paramiko.rsakey.RSAKey
            elif self.ssh_key_type == "ECDSA":
                key_class = paramiko.ecdsakey.ECDSAKey
            elif self.ssh_key_type == "Ed25519":
                key_class = paramiko.ed25519key.Ed25519Key
            key = key_class.from_private_key(
                io.StringIO(self.ssh_key),
                password=self.ssh_password)
            client.connect(hostname=self.ip_address,
                           username=self.ssh_username,
                           pkey=key,
                           allow_agent=False,
                           look_for_keys=False)

        client.exec_command(command)

        client.close()

    def shutdown(self):
        if not self.shutdown_available:
            raise DeviceError("Shutdown is not available for this device")
        self._exec_ssh_command(self.shutdown_command)

    def reboot(self):
        if not self.reboot_available:
            raise DeviceError("Reboot is not available for this device")
        self._exec_ssh_command(self.reboot_command)

    def logout(self):
        if not self.logout_available:
            raise DeviceError("Logout is not available for this device")
        self._exec_ssh_command(self.logout_command)

    def sleep(self):
        if not self.sleep_available:
            raise DeviceError("Sleep is not available for this device")
        self._exec_ssh_command(self.sleep_command)

    def hibernate(self):
        if not self.hibernate_available:
            raise DeviceError("Hibernate is not available for this device")
        self._exec_ssh_command(self.hibernate_command)

    def edit(self, name, mac_address, ip_address, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("UPDATE devices SET name = %s, mac_address = %s, ip_address = %s, shutdown_command = %s, reboot_command = %s, logout_command = %s, sleep_command = %s, hibernate_command = %s WHERE id = %s", (name, mac_address, ip_address, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command, self.device_id, ))
        db.commit()
        cursor.close()
        db.close()

    def edit_credentials(self, ssh_username, ssh_key_type, ssh_key, ssh_password):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("UPDATE devices SET ssh_username = %s, ssh_key_type = %s, ssh_key = %s, ssh_password = %s WHERE id = %s", (ssh_username, ssh_key_type, ssh_key, ssh_password, self.device_id, ))
        db.commit()
        cursor.close()
        db.close()

    def delete(self):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM devices WHERE id = %s", (self.device_id, ))
        db.commit()
        cursor.close()
        db.close()

    @staticmethod
    def create(user, name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command):
        db = mysql.connector.connect(**mysql_configs)
        cursor = db.cursor(dictionary=True)
        cursor.execute("INSERT INTO devices (user_id, name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (user.user_id, name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command, ))
        device_id = cursor.lastrowid
        db.commit()
        cursor.close()
        db.close()
        return Device(device_id)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_alternative_id(user_id)
    except UserError:
        return None


@login_manager.request_loader
def load_user_from_request(request):
    authorization_header = request.headers.get("Authorization", "")
    if authorization_header.startswith("Bearer "):
        try:
            return User.get_by_access_token(authorization_header.split(" ")[1])
        except Exception:
            return None
    return None


@app.route("/favicon.ico")
def favicon():
    return send_file("static/img/icon.ico")


@app.route("/manifest.json")
def manifest():
    return send_file("static/manifest.json")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def login_api():
    username = request.json.get("username")
    password = request.json.get("password")
    otp = request.json.get("otp")

    if username is None or password is None:
        return {"status": "error", "error": "username_and_password_required"}

    user = User.get_by_username(username)

    if user is None:
        return {"status": "error", "error": "wrong_username_or_password"}

    if not user.check_password(password):
        return {"status": "error", "error": "wrong_username_or_password"}

    if user.enabled_2fa and otp is None:
        return {"status": "error", "error": "otp_required"}

    if user.enabled_2fa and not user.verify_otp(otp):
        return {"status": "error", "error": "wrong_otp"}

    login_user(user, remember=True)

    return {"status": "ok"}


@app.route("/api/user", methods=["PUT"])
@login_required
def edit_current_user():
    username = request.json.get("username")
    email = request.json.get("email")

    if username is not None and username != current_user.username:
        if User.get_by_username(username) is None:
            current_user.change_username(username)
        else:
            return {"status": "error", "error": "username_taken"}

    if email is not None and email != "" and email != current_user.email:
        current_user.change_email(email)

    return {"status": "ok"}


@app.route("/api/user/password", methods=["PUT"])
@login_required
def change_password():
    password = request.json.get("password")
    if password is None or password == "":
        return {"status": "error", "error": "password_required"}

    username = current_user.username
    current_user.change_password(password)
    login_user(User.get_by_username(username))

    return {"status": "ok"}


@app.route("/api/user/2fa")
@login_required
def get_2fa():
    return {"status": "ok", "secret": current_user.totp_secret}


@app.route("/api/user/2fa", methods=["POST"])
@login_required
def enable_2fa():
    current_user.enable_2fa()
    return {"status": "ok"}


@app.route("/api/user/2fa", methods=["DELETE"])
@login_required
def disable_2fa():
    current_user.disable_2fa()
    return {"status": "ok"}


@app.route("/api/user/access_tokens")
@login_required
def get_access_tokens():
    return {"status": "ok", "access_tokens": current_user.access_tokens}


@app.route("/api/user/access_tokens", methods=["POST"])
@login_required
def create_access_token():
    name = request.json.get("name")

    if name is None or name == "":
        return {"status": "error", "error": "name_required"}

    token = current_user.create_access_token(name)

    return {"status": "ok", "token": token}


@app.route("/api/device", methods=["POST"])
@login_required
def create_device():
    name = request.json.get("name")
    mac_address = request.json.get("mac_address")
    ip_address = request.json.get("ip_address")
    ssh_username = request.json.get("ssh_username")
    ssh_key_type = request.json.get("ssh_key_type")
    ssh_key = request.json.get("ssh_key")
    ssh_password = request.json.get("ssh_password")
    shutdown_command = request.json.get("shutdown_command")
    reboot_command = request.json.get("reboot_command")
    logout_command = request.json.get("logout_command")
    sleep_command = request.json.get("sleep_command")
    hibernate_command = request.json.get("hibernate_command")

    current_user.create_device(name, mac_address, ip_address, ssh_username, ssh_key_type, ssh_key, ssh_password, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command)

    return {"status": "ok"}


@app.route("/api/device/<device_id>", methods=["PUT"])
@login_required
def edit_device(device_id):
    name = request.json.get("name")
    mac_address = request.json.get("mac_address")
    ip_address = request.json.get("ip_address")
    shutdown_command = request.json.get("shutdown_command")
    reboot_command = request.json.get("reboot_command")
    logout_command = request.json.get("logout_command")
    sleep_command = request.json.get("sleep_command")
    hibernate_command = request.json.get("hibernate_command")

    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    device.edit(name, mac_address, ip_address, shutdown_command, reboot_command, logout_command, sleep_command, hibernate_command)

    return {"status": "ok"}


@app.route("/api/device/<device_id>/credentials", methods=["PUT"])
@login_required
def edit_device_credentials(device_id):
    ssh_username = request.json.get("ssh_username")
    ssh_key_type = request.json.get("ssh_key_type")
    ssh_key = request.json.get("ssh_key")
    ssh_password = request.json.get("ssh_password")

    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    device.edit_credentials(ssh_username, ssh_key_type, ssh_key, ssh_password)

    return {"status": "ok"}


@app.route("/api/device/<device_id>", methods=["DELETE"])
@login_required
def delete_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    device.delete()

    return {"status": "ok"}


@app.route("/api/device/<device_id>/wake", methods=["POST"])
@login_required
def wake_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.wake_available:
        return {"status": "error", "error": "wake_not_available"}

    device.wake()

    return {"status": "ok"}


@app.route("/api/device/<device_id>/shutdown", methods=["POST"])
@login_required
def shutdown_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.shutdown_available:
        return {"status": "error", "error": "shutdown_not_available"}

    try:
        device.shutdown()
    except Exception:
        return {"status": "error", "error": "ssh_error"}

    return {"status": "ok"}


@app.route("/api/device/<device_id>/reboot", methods=["POST"])
@login_required
def reboot_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.reboot_available:
        return {"status": "error", "error": "reboot_not_available"}

    try:
        device.reboot()
    except Exception:
        return {"status": "error", "error": "ssh_error"}

    return {"status": "ok"}


@app.route("/api/device/<device_id>/logout", methods=["POST"])
@login_required
def logout_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.logout_available:
        return {"status": "error", "error": "logout_not_available"}

    try:
        device.logout()
    except Exception:
        return {"status": "error", "error": "ssh_error"}

    return {"status": "ok"}


@app.route("/api/device/<device_id>/sleep", methods=["POST"])
@login_required
def sleep_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.sleep_available:
        return {"status": "error", "error": "sleep_not_available"}

    try:
        device.sleep()
    except Exception:
        return {"status": "error", "error": "ssh_error"}

    return {"status": "ok"}


@app.route("/api/device/<device_id>/hibernate", methods=["POST"])
@login_required
def hibernate_device(device_id):
    try:
        device = Device(device_id)
    except DeviceError:
        return {"status": "error", "error": "device_not_found"}

    if current_user.user_id != device.user.user_id:
        return {"status": "error", "error": "access_denied"}

    if not device.hibernate_available:
        return {"status": "error", "error": "hibernate_not_available"}

    try:
        device.hibernate()
    except Exception:
        return {"status": "error", "error": "ssh_error"}

    return {"status": "ok"}


@app.route("/api/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(401)
def unauthorized(e):
    return redirect(url_for('login'))


if __name__ == "__main__":
    host = configs["host"] if "host" in configs.keys() else None
    port = configs["port"] if "port" in configs.keys() else None
    debug = configs["debug"] if "debug" in configs.keys() else None

    app.run(host=host, port=port, debug=debug)
