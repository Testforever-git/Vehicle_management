from flask import render_template, redirect, url_for
from . import bp
from ...security.mock_users import get_current_user


def _require_admin():
    u = get_current_user()
    return u.is_authenticated and u.role_code == "admin"


@bp.get("/users")
def user_list():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    return render_template("admin/users.html", active_menu="admin_users", users=[])


@bp.get("/field-permissions")
def field_permissions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    return render_template(
        "admin/field_permissions.html",
        active_menu="field_permissions",
        field_permissions=[],
        role_codes=["viewer", "sales", "engineer", "finance", "admin"],
    )
