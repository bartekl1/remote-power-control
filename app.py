from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import mysql.connector
import pyotp

import json
import random
import time
import string
import hashlib

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


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_alternative_id(user_id)
    except UserError:
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
