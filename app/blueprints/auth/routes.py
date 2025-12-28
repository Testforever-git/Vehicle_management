from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash
from . import bp
from ...repositories.user_repo import get_user_by_username
from ...security.users import login_user, logout


@bp.get("/login")
def login():
    return render_template("auth/login.html", active_menu="")


@bp.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if not username or not password:
        flash("username and password required", "warning")
        return redirect(url_for("auth.login"))
    user = get_user_by_username(username)
    if not user or not user.get("is_active"):
        flash("invalid credentials", "danger")
        return redirect(url_for("auth.login"))
    if not check_password_hash(user["password_hash"], password):
        flash("invalid credentials", "danger")
        return redirect(url_for("auth.login"))
    login_user(user["id"])
    return redirect(url_for("ui.dashboard"))


@bp.get("/logout")
def logout_route():
    logout()
    return redirect(url_for("auth.login"))
