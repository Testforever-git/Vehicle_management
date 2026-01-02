from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from . import bp
from ...repositories.user_repo import get_user_by_username
from ...security.users import login_user, logout, get_current_user
from ...repositories.audit_log_repo import create_audit_log


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
    create_audit_log(
        None,
        actor="user",
        actor_id=user["id"],
        action_type="login",
        action_detail={
            "op": "login",
            "context": {
                "ip": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
            },
            "message": "登录",
        },
    )
    next_url = session.pop("next_url", None)
    if next_url:
        return redirect(next_url)
    return redirect(url_for("ui.dashboard"))


@bp.get("/logout")
def logout_route():
    current_user = get_current_user()
    if current_user.is_authenticated:
        create_audit_log(
            None,
            actor="user",
            actor_id=current_user.user_id,
            action_type="logout",
            action_detail={
                "op": "logout",
                "context": {
                    "ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent"),
                },
                "message": "登出",
            },
        )
    logout()
    return redirect(url_for("auth.login"))
