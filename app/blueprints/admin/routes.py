from flask import render_template, redirect, url_for, request, flash
from . import bp
from ...repositories.field_permission_repo import (
    list_field_catalog,
    list_field_permissions_admin,
    refresh_field_catalog,
    upsert_field_permission,
    update_field_permission,
    delete_field_permission,
)
from ...repositories.role_repo import list_roles
from ...repositories.user_repo import create_user, list_users, update_password, update_user, soft_delete_user
from ...repositories.vehicle_log_repo import log_vehicle_action
from ...repositories.master_data_repo import (
    list_brands,
    list_models,
    list_colors,
    list_enums,
    create_brand,
    update_brand,
    deactivate_brand,
    create_model,
    update_model,
    deactivate_model,
    create_color,
    update_color,
    deactivate_color,
    create_enum,
    update_enum,
    deactivate_enum,
)
from ...security.users import get_current_user
from werkzeug.security import generate_password_hash

SYSTEM_FIELDS = {
    "id",
    "created_at",
    "created_by",
    "created_date",
    "updated_at",
    "updated_by",
    "updated_date",
}


def _require_admin():
    u = get_current_user()
    return u.is_authenticated and u.role_code == "admin"


def _catalog_map(field_catalog):
    catalog = {}
    for row in field_catalog:
        catalog.setdefault(row["table_name"], set()).add(row["field_name"])
    return catalog


def _logical_field_name(table_fields, field_name: str) -> str:
    if field_name.endswith(("_cn", "_jp")):
        base = field_name[:-3]
        if f"{base}_cn" in table_fields and f"{base}_jp" in table_fields:
            return base
    return field_name


def _actual_fields(table_fields, logical_field: str):
    candidates = [logical_field, f"{logical_field}_cn", f"{logical_field}_jp"]
    return [name for name in candidates if name in table_fields]


def _logical_fields_for_table(table_fields):
    logical_fields = []
    seen = set()
    for field_name in sorted(table_fields):
        if field_name in SYSTEM_FIELDS:
            continue
        logical_name = _logical_field_name(table_fields, field_name)
        if logical_name in SYSTEM_FIELDS or logical_name in seen:
            continue
        seen.add(logical_name)
        logical_fields.append(logical_name)
    return logical_fields


def _admin_role_id(roles):
    for role in roles:
        if role["role_code"] == "admin":
            return role["id"]
    return None


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
    admin_role_id = _admin_role_id(roles)
    roles = [role for role in roles if role["role_code"] != "admin"]
    field_catalog = list_field_catalog()
    field_permissions = list_field_permissions_admin()
    selected_role_id = request.args.get("role_id", "").strip()
    catalog_map = _catalog_map(field_catalog)
    table_names = sorted(catalog_map.keys())
    logical_field_catalog = []
    for table_name in table_names:
        for logical_name in _logical_fields_for_table(catalog_map[table_name]):
            logical_field_catalog.append({"table_name": table_name, "field_name": logical_name})
    grouped_permissions = {}
    for row in field_permissions:
        if row["role_id"] == admin_role_id:
            continue
        table_fields = catalog_map.get(row["table_name"], set())
        if row["field_name"] in SYSTEM_FIELDS:
            continue
        logical_name = _logical_field_name(table_fields, row["field_name"])
        if logical_name in SYSTEM_FIELDS:
            continue
        key = (row["role_id"], row["table_name"], logical_name)
        existing = grouped_permissions.get(key)
        if not existing:
            grouped_permissions[key] = {
                "role_id": row["role_id"],
                "role_code": row["role_code"],
                "name_cn": row["name_cn"],
                "name_jp": row["name_jp"],
                "table_name": row["table_name"],
                "field_name": logical_name,
                "access_level": row["access_level"],
                "description": row["description"],
            }
        else:
            existing["access_level"] = max(existing["access_level"], row["access_level"])
            if not existing["description"] and row["description"]:
                existing["description"] = row["description"]
    grouped_list = sorted(
        grouped_permissions.values(),
        key=lambda item: (item["role_code"], item["table_name"], item["field_name"]),
    )
    if selected_role_id:
        grouped_list = [
            item for item in grouped_list if str(item["role_id"]) == selected_role_id
        ]
    return render_template(
        "admin/field_permissions.html",
        active_menu="field_permissions",
        field_permissions=grouped_list,
        roles=roles,
        field_catalog=logical_field_catalog,
        table_names=table_names,
        access_levels=[10, 20],
        selected_role_id=selected_role_id,
    )


@bp.post("/field-permissions")
def update_field_permissions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    action = request.form.get("action", "update")
    roles = list_roles()
    admin_role_id = _admin_role_id(roles)

    if action == "bulk_update":
        role_ids = [int(rid) for rid in request.form.getlist("role_id")]
        table_names = request.form.getlist("table_name")
        field_names = request.form.getlist("field_name")
        access_levels = [int(level) for level in request.form.getlist("access_level")]
        descriptions = request.form.getlist("description")
        if not (
            len(role_ids)
            == len(table_names)
            == len(field_names)
            == len(access_levels)
            == len(descriptions)
        ):
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))

        field_catalog = list_field_catalog()
        catalog_map = _catalog_map(field_catalog)
        for role_id, table_name, field_name, access_level, description in zip(
            role_ids,
            table_names,
            field_names,
            access_levels,
            descriptions,
        ):
            if role_id == admin_role_id:
                continue
            table_name = table_name.strip()
            field_name = field_name.strip()
            if not role_id or not table_name or not field_name:
                continue
            table_fields = catalog_map.get(table_name, set())
            for actual_field in _actual_fields(table_fields, field_name):
                if actual_field in SYSTEM_FIELDS:
                    delete_field_permission(role_id, table_name, actual_field)
                    continue
                if access_level < 10:
                    delete_field_permission(role_id, table_name, actual_field)
                    continue
                upsert_field_permission(
                    role_id,
                    table_name,
                    actual_field,
                    access_level,
                    description.strip(),
                )
                log_vehicle_action(
                    None,
                    actor=get_current_user().username,
                    action_type="field_permission_update",
                    action_detail={
                        "role_id": role_id,
                        "table_name": table_name,
                        "field_name": actual_field,
                        "access_level": access_level,
                    },
                    source_module="admin",
                )
        flash("field permission updated", "success")
        return redirect(url_for("admin.field_permissions"))

    if action == "bulk_delete":
        selected_rows = {int(idx) for idx in request.form.getlist("row_select")}
        role_ids = [int(rid) for rid in request.form.getlist("role_id")]
        table_names = request.form.getlist("table_name")
        field_names = request.form.getlist("field_name")
        if not (
            len(role_ids) == len(table_names) == len(field_names)
        ):
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))

        field_catalog = list_field_catalog()
        catalog_map = _catalog_map(field_catalog)
        for index, (role_id, table_name, field_name) in enumerate(
            zip(role_ids, table_names, field_names)
        ):
            if index not in selected_rows:
                continue
            if role_id == admin_role_id:
                continue
            table_name = table_name.strip()
            field_name = field_name.strip()
            if not role_id or not table_name or not field_name:
                continue
            table_fields = catalog_map.get(table_name, set())
            for actual_field in _actual_fields(table_fields, field_name):
                delete_field_permission(role_id, table_name, actual_field)
                log_vehicle_action(
                    None,
                    actor=get_current_user().username,
                    action_type="field_permission_delete",
                    action_detail={
                        "role_id": role_id,
                        "table_name": table_name,
                        "field_name": actual_field,
                    },
                    source_module="admin",
                )
        flash("field permission deleted", "success")
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
        if role_id == admin_role_id:
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))
        if access_level < 10:
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))
        field_catalog = list_field_catalog()
        catalog_map = _catalog_map(field_catalog)
        table_fields = catalog_map.get(table_name, set())
        if field_name == "__all__":
            field_names = _logical_fields_for_table(table_fields)
        else:
            field_names = [field_name]
        for logical_field in field_names:
            for actual_field in _actual_fields(table_fields, logical_field):
                if actual_field in SYSTEM_FIELDS:
                    continue
                upsert_field_permission(
                    role_id,
                    table_name,
                    actual_field,
                    access_level,
                    description,
                )
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
        field_catalog = list_field_catalog()
        catalog_map = _catalog_map(field_catalog)
        table_fields = catalog_map.get(table_name, set())
        if role_id == admin_role_id:
            flash("invalid field permission update", "warning")
            return redirect(url_for("admin.field_permissions"))
        for actual_field in _actual_fields(table_fields, field_name):
            if actual_field in SYSTEM_FIELDS:
                delete_field_permission(role_id, table_name, actual_field)
                continue
            if access_level < 10:
                delete_field_permission(role_id, table_name, actual_field)
                continue
            upsert_field_permission(role_id, table_name, actual_field, access_level, description)
        log_vehicle_action(
            None,
            actor=get_current_user().username,
            action_type="field_permission_update",
            action_detail={
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


@bp.get("/dictionaries")
def dictionaries():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    return render_template(
        "admin/dictionaries.html",
        active_menu="admin_dictionaries",
        brands=list_brands(),
        models=list_models(),
        colors=list_colors(),
        enums=list_enums(),
    )


@bp.post("/dictionaries")
def dictionary_actions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    action = request.form.get("action")
    dict_type = request.form.get("dict_type")

    if dict_type == "brand":
        brand_code = request.form.get("brand_code", "").strip()
        name_cn = request.form.get("name_cn", "").strip()
        name_jp = request.form.get("name_jp", "").strip()
        is_active = request.form.get("is_active") == "1"
        if action == "create" and brand_code:
            create_brand(brand_code, name_cn, name_jp, is_active)
        elif action == "update":
            brand_id = int(request.form.get("brand_id", "0") or 0)
            if brand_id:
                update_brand(brand_id, brand_code, name_cn, name_jp, is_active)
        elif action == "delete":
            brand_id = int(request.form.get("brand_id", "0") or 0)
            if brand_id:
                deactivate_brand(brand_id)
    elif dict_type == "model":
        model_code = request.form.get("model_code", "").strip()
        name_cn = request.form.get("name_cn", "").strip()
        name_jp = request.form.get("name_jp", "").strip()
        brand_id = int(request.form.get("brand_id", "0") or 0)
        is_active = request.form.get("is_active") == "1"
        if action == "create" and model_code and brand_id:
            create_model(brand_id, model_code, name_cn, name_jp, is_active)
        elif action == "update":
            model_id = int(request.form.get("model_id", "0") or 0)
            if model_id and brand_id:
                update_model(model_id, brand_id, model_code, name_cn, name_jp, is_active)
        elif action == "delete":
            model_id = int(request.form.get("model_id", "0") or 0)
            if model_id:
                deactivate_model(model_id)
    elif dict_type == "color":
        color_code = request.form.get("color_code", "").strip()
        name_cn = request.form.get("name_cn", "").strip()
        name_jp = request.form.get("name_jp", "").strip()
        is_active = request.form.get("is_active") == "1"
        if action == "create" and color_code:
            create_color(color_code, name_cn, name_jp, is_active)
        elif action == "update":
            color_id = int(request.form.get("color_id", "0") or 0)
            if color_id:
                update_color(color_id, color_code, name_cn, name_jp, is_active)
        elif action == "delete":
            color_id = int(request.form.get("color_id", "0") or 0)
            if color_id:
                deactivate_color(color_id)
    elif dict_type == "enum":
        enum_type = request.form.get("enum_type", "").strip()
        enum_code = request.form.get("enum_code", "").strip()
        name_cn = request.form.get("name_cn", "").strip()
        name_jp = request.form.get("name_jp", "").strip()
        is_active = request.form.get("is_active") == "1"
        if action == "create" and enum_type and enum_code:
            create_enum(enum_type, enum_code, name_cn, name_jp, is_active)
        elif action == "update":
            enum_id = int(request.form.get("enum_id", "0") or 0)
            if enum_id:
                update_enum(enum_id, enum_type, enum_code, name_cn, name_jp, is_active)
        elif action == "delete":
            enum_id = int(request.form.get("enum_id", "0") or 0)
            if enum_id:
                deactivate_enum(enum_id)

    return redirect(url_for("admin.dictionaries", lang=request.args.get("lang")))
