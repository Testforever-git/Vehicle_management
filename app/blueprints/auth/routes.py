from flask import render_template, request, redirect, url_for, flash
from . import bp
from ...security.mock_users import login_as, logout


@bp.get("/login")
def login():
    return render_template("auth/login.html", active_menu="")


@bp.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    role_code = request.form.get("role_code", "viewer").strip()
    if not username:
        flash("username required", "warning")
        return redirect(url_for("auth.login"))
    login_as(username=username, role_code=role_code)
    return redirect(url_for("ui.dashboard"))


@bp.get("/logout")
def logout_route():
    logout()
    return redirect(url_for("auth.login"))
