from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import mysql.connector

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
        self.profile_picture_url = f"https://gravatar.com/avatar/{hashlib.sha256(self.email.strip().lower().encode('utf-8')).hexdigest()}?s=200&d=mp"

    def get_id(self):
        return self.alternative_id

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

        db = mysql.connector.connect(**configs['mysql'])
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET alternative_id = %s, password_hash = %s WHERE id = %s", (self.alternative_id, self.password_hash, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def change_username(self, new_username):
        db = mysql.connector.connect(**configs['mysql'])
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET username = %s WHERE id = %s", (new_username, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    def change_email(self, new_email):
        db = mysql.connector.connect(**configs['mysql'])
        cursor = db.cursor(dictionary=True)

        cursor.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, self.user_id))

        db.commit()
        cursor.close()
        db.close()

    @staticmethod
    def get_by_username(username):
        return None


def get_user(alternative_id=None, username=None):
    db = mysql.connector.connect(**configs['mysql'])
    cursor = db.cursor(dictionary=True)

    if alternative_id is not None:
        cursor.execute("SELECT * FROM users WHERE alternative_id = %s LIMIT 1", (alternative_id, ))
    elif username is not None:
        cursor.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username, ))
    else:
        return None

    result = cursor.fetchall()
    cursor.close()
    db.close()

    if len(result) == 1:
        return User(user_id=result[0]["id"],
                    alternative_id=result[0]["alternative_id"],
                    username=result[0]["username"],
                    password_hash=result[0]["password_hash"],
                    email=result[0]["email"])
    return None


@login_manager.user_loader
def load_user(user_id):
    return get_user(alternative_id=user_id)


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


@app.route("/logout")
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
