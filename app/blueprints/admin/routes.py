from flask import render_template, redirect, url_for, request, flash
from . import bp
from ...repositories.field_permission_repo import list_field_permissions, update_field_permission
from ...repositories.role_repo import list_roles
from ...repositories.user_repo import create_user, list_users, update_password, update_user, soft_delete_user
from ...repositories.vehicle_log_repo import log_vehicle_action
from ...security.users import get_current_user
from werkzeug.security import generate_password_hash


def _require_admin():
    u = get_current_user()
    return u.is_authenticated and u.role_code == "admin"


@bp.get("/users")
def user_list():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    users = list_users()
    roles = list_roles()
    return render_template("admin/users.html", active_menu="admin_users", users=users, roles=roles)


@bp.post("/users")
def user_actions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    action = request.form.get("action")
    if action == "create":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "").strip()
        role_id = int(request.form.get("role_id", "0") or 0)
        is_active = request.form.get("is_active") == "1"
        if not username or not password or not role_id:
            flash("missing required fields", "warning")
        else:
            create_user(username, generate_password_hash(password), role_id, full_name, is_active)
            log_vehicle_action(
                None,
                actor=get_current_user().username,
                action_type="user_create",
                action_detail={"username": username, "role_id": role_id, "is_active": is_active},
                source_module="admin",
            )
            flash("user created", "success")
    elif action == "update":
        user_id = int(request.form.get("user_id", "0") or 0)
        role_id = int(request.form.get("role_id", "0") or 0)
        full_name = request.form.get("full_name", "").strip()
        is_active = request.form.get("is_active") == "1"
        password = request.form.get("password", "").strip()
        if user_id and role_id:
            update_user(user_id, role_id, is_active, full_name)
            if password:
                update_password(user_id, generate_password_hash(password))
            log_vehicle_action(
                None,
                actor=get_current_user().username,
                action_type="user_update",
                action_detail={
                    "user_id": user_id,
                    "role_id": role_id,
                    "is_active": is_active,
                    "password_changed": bool(password),
                },
                source_module="admin",
            )
            flash("user updated", "success")
        else:
            flash("invalid user update", "warning")
    elif action == "delete":
        user_id = int(request.form.get("user_id", "0") or 0)
        if user_id:
            soft_delete_user(user_id)
            log_vehicle_action(
                None,
                actor=get_current_user().username,
                action_type="user_delete",
                action_detail={"user_id": user_id},
                source_module="admin",
            )
            flash("user deleted", "success")
        else:
            flash("invalid user delete", "warning")
    return redirect(url_for("admin.user_list"))


@bp.get("/field-permissions")
def field_permissions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    roles = list_roles()
    field_permissions = list_field_permissions()
    return render_template(
        "admin/field_permissions.html",
        active_menu="field_permissions",
        field_permissions=field_permissions,
        roles=roles,
        access_levels=["basic", "advanced", "admin"],
    )


@bp.post("/field-permissions")
def update_field_permissions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    permission_id = int(request.form.get("permission_id", "0") or 0)
    access_level = request.form.get("access_level", "basic")
    min_role_code = request.form.get("min_role_code", "user")
    is_visible = request.form.get("is_visible") == "1"
    is_editable = request.form.get("is_editable") == "1"
    description = request.form.get("description", "").strip()
    if permission_id:
        update_field_permission(
            permission_id,
            access_level,
            min_role_code,
            is_visible,
            is_editable,
            description,
        )
        log_vehicle_action(
            None,
            actor=get_current_user().username,
            action_type="field_permission_update",
            action_detail={
                "permission_id": permission_id,
                "access_level": access_level,
                "min_role_code": min_role_code,
                "is_visible": is_visible,
                "is_editable": is_editable,
            },
            source_module="admin",
        )
        flash("field permission updated", "success")
    else:
        flash("invalid field permission update", "warning")
    return redirect(url_for("admin.field_permissions"))
