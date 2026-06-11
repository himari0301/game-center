import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_user_by_username, create_user, get_best_records_all, get_ranking_all, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "numeron-secret-key-2024")

login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return User(user["id"], user["username"]) if user else None

@app.route("/")
def top():
    version = os.environ.get("RENDER_GIT_COMMIT", "local")[:7]
    branch = os.environ.get("RENDER_GIT_BRANCH", "dev")
    return render_template("top.html", version=version, branch=branch)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = get_user_by_username(username)
        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"]))
            return redirect(url_for("top"))
        flash("ユーザー名またはパスワードが違います")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("top"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("ユーザー名とパスワードを入力してください")
        elif len(username) < 2 or len(username) > 20:
            flash("ユーザー名は2〜20文字にしてください")
        elif len(password) < 4:
            flash("パスワードは4文字以上にしてください")
        elif not create_user(username, generate_password_hash(password)):
            flash("そのユーザー名はすでに使われています")
        else:
            flash("登録完了！ログインしてください")
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/numeron/howto")
def howto():
    return render_template("numeron_howto.html")

@app.route("/countdown/howto")
def countdown_howto():
    return render_template("countdown_howto.html")

@app.route("/ranking")
def ranking():
    return render_template("ranking.html",
        rankings=get_ranking_all(),
        current_game=request.args.get("game", "numeron"),
        current_difficulty=request.args.get("difficulty", "easy"),
        from_page=request.args.get("from", "")
    )

@app.route("/my_records")
@login_required
def my_records():
    return render_template("my_records.html",
        records=get_best_records_all(current_user.id),
        from_page=request.args.get("from", "")
    )

from numeron_app import numeron_bp
from countdown_app import countdown_bp
app.register_blueprint(numeron_bp)
app.register_blueprint(countdown_bp)

init_db()

if __name__ == "__main__":
    app.run(debug=True)