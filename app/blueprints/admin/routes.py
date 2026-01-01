from flask import render_template, redirect, url_for, request, flash
from . import bp
from ...repositories.field_permission_repo import (
    list_field_catalog,
    list_field_permissions_admin,
    refresh_field_catalog,
    upsert_field_permission,
    update_field_permission,
)
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
    refresh_field_catalog()
    roles = list_roles()
    field_catalog = list_field_catalog()
    field_permissions = list_field_permissions_admin()
    table_names = sorted({row["table_name"] for row in field_catalog})
    return render_template(
        "admin/field_permissions.html",
        active_menu="field_permissions",
        field_permissions=field_permissions,
        roles=roles,
        field_catalog=field_catalog,
        table_names=table_names,
        access_levels=[0, 10, 20],
    )


@bp.post("/field-permissions")
def update_field_permissions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    action = request.form.get("action", "update")

    if action == "bulk_update":
        permission_ids = [int(pid) for pid in request.form.getlist("permission_id") if pid]
        role_ids = [int(rid) for rid in request.form.getlist("role_id")]
        table_names = request.form.getlist("table_name")
        field_names = request.form.getlist("field_name")
        access_levels = [int(level) for level in request.form.getlist("access_level")]
        descriptions = request.form.getlist("description")

        if not (
            len(permission_ids)
            == len(role_ids)
            == len(table_names)
            == len(field_names)
            == len(access_levels)
            == len(descriptions)
        ):
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))

        for permission_id, role_id, table_name, field_name, access_level, description in zip(
            permission_ids,
            role_ids,
            table_names,
            field_names,
            access_levels,
            descriptions,
        ):
            update_field_permission(
                permission_id,
                role_id,
                table_name.strip(),
                field_name.strip(),
                access_level,
                description.strip(),
            )
            log_vehicle_action(
                None,
                actor=get_current_user().username,
                action_type="field_permission_update",
                action_detail={
                    "permission_id": permission_id,
                    "role_id": role_id,
                    "table_name": table_name,
                    "field_name": field_name,
                    "access_level": access_level,
                },
                source_module="admin",
            )
        flash("field permission updated", "success")
        return redirect(url_for("admin.field_permissions"))
    permission_id = int(request.form.get("permission_id", "0") or 0)
    role_id = int(request.form.get("role_id", "0") or 0)
    table_name = request.form.get("table_name", "").strip()
    field_name = request.form.get("field_name", "").strip()
    access_level = int(request.form.get("access_level", "0") or 0)
    description = request.form.get("description", "").strip()

    if not role_id or not table_name or not field_name:
        flash("invalid field permission update", "warning")
        return redirect(url_for("admin.field_permissions"))

    if action == "create":
        upsert_field_permission(role_id, table_name, field_name, access_level, description)
        log_vehicle_action(
            None,
            actor=get_current_user().username,
            action_type="field_permission_create",
            action_detail={
                "role_id": role_id,
                "table_name": table_name,
                "field_name": field_name,
                "access_level": access_level,
            },
            source_module="admin",
        )
        flash("field permission created", "success")
        return redirect(url_for("admin.field_permissions"))

    if permission_id:
        update_field_permission(
            permission_id,
            role_id,
            table_name,
            field_name,
            access_level,
            description,
        )
        log_vehicle_action(
            None,
            actor=get_current_user().username,
            action_type="field_permission_update",
            action_detail={
                "permission_id": permission_id,
                "role_id": role_id,
                "table_name": table_name,
                "field_name": field_name,
                "access_level": access_level,
            },
            source_module="admin",
        )
        flash("field permission updated", "success")
    else:
        flash("invalid field permission update", "warning")
    return redirect(url_for("admin.field_permissions"))
