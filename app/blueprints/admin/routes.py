import json

from flask import render_template, redirect, url_for, request, flash
from . import bp
from ...repositories.field_permission_repo import (
    field_permission_exists,
    list_field_catalog,
    list_field_permissions_admin,
    refresh_field_catalog,
    upsert_field_permission,
    update_field_permission,
    delete_field_permission,
)
from ...repositories.role_repo import list_roles
from ...repositories.user_repo import create_user, list_users, update_password, update_user, soft_delete_user
from ...repositories.customer_repo import list_customers, count_customers, soft_delete_customers
from ...repositories.vehicle_log_repo import log_vehicle_action
from ...repositories.audit_log_repo import create_audit_log, count_audit_logs, list_audit_logs
from ...repositories.audit_setting_repo import (
    list_audit_catalog,
    update_audit_flags,
    update_table_audit_flag,
)
from ...repositories.rental_pricing_repo import list_rental_pricing, upsert_rental_pricing
from ...repositories.rental_request_repo import list_rental_requests
from ...repositories.rental_service_repo import (
    list_rental_services,
    create_rental_service,
    update_rental_service,
)
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


def _parse_int(value: str | None, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(value: str | None, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@bp.get("/users")
def user_list():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    users = list_users()
    roles = list_roles()
    return render_template("admin/users.html", active_menu="admin_users", users=users, roles=roles)


@bp.get("/customers")
def customer_list():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    page = max(int(request.args.get("page", 1)), 1)
    per_page = int(request.args.get("per_page", 20))
    if per_page not in (20, 50):
        per_page = 20
    customers = list_customers(page=page, per_page=per_page)
    total = count_customers()
    total_pages = max((total + per_page - 1) // per_page, 1)
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
    return render_template(
        "admin/customers.html",
        active_menu="admin_customers",
        customers=customers,
        pagination=pagination,
    )


@bp.post("/customers/delete")
def customer_delete():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    customer_ids = request.form.getlist("customer_ids")
    ids = [int(cid) for cid in customer_ids if str(cid).isdigit()]
    soft_delete_customers(ids)
    return redirect(url_for("admin.customer_list", lang=request.args.get("lang")))


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
    try:
        page = int(request.args.get("page", "1") or 1)
    except ValueError:
        page = 1
    if page < 1:
        page = 1
    try:
        per_page = int(request.args.get("per_page", "20") or 20)
    except ValueError:
        per_page = 20
    if per_page not in {20, 50}:
        per_page = 20
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
    total = len(grouped_list)
    total_pages = max((total + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * per_page
    end = start + per_page
    paged_list = grouped_list[start:end]
    return render_template(
        "admin/field_permissions.html",
        active_menu="field_permissions",
        field_permissions=paged_list,
        roles=roles,
        field_catalog=logical_field_catalog,
        table_names=table_names,
        access_levels=[10, 20],
        selected_role_id=selected_role_id,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
    )


@bp.get("/audit-log")
def audit_log():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    refresh_field_catalog()
    try:
        page = int(request.args.get("page", "1") or 1)
    except ValueError:
        page = 1
    if page < 1:
        page = 1
    try:
        per_page = int(request.args.get("per_page", "20") or 20)
    except ValueError:
        per_page = 20
    if per_page not in {20, 50}:
        per_page = 20

    field_catalog = list_audit_catalog()
    catalog_map = {}
    table_audit_flags = {}
    audit_flags = {}
    for row in field_catalog:
        table_name = row["table_name"]
        field_name = row["field_name"]
        is_audited = bool(row["is_audited"])
        audit_flags[(table_name, field_name)] = is_audited
        if field_name == "__TABLE__":
            table_audit_flags[table_name] = is_audited
            continue
        catalog_map.setdefault(table_name, set()).add(field_name)

    audit_tables = []
    for table_name in sorted(catalog_map.keys()):
        table_fields = catalog_map[table_name]
        logical_fields = []
        for logical_name in _logical_fields_for_table(table_fields):
            actual_fields = _actual_fields(table_fields, logical_name)
            is_audited = all(
                audit_flags.get((table_name, field_name), False)
                for field_name in actual_fields
            )
            logical_fields.append(
                {"name": logical_name, "is_audited": is_audited}
            )
        audit_tables.append(
            {
                "table_name": table_name,
                "table_audited": table_audit_flags.get(table_name, False),
                "fields": logical_fields,
            }
        )

    total_logs = count_audit_logs()
    total_pages = max((total_logs + per_page - 1) // per_page, 1)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    audit_logs = list_audit_logs(per_page, offset)
    for row in audit_logs:
        if row["actor"] == "user":
            row["actor_label"] = row["full_name"] or row["username"] or "-"
        else:
            row["actor_label"] = row["actor"]

    return render_template(
        "admin/audit_log.html",
        active_menu="audit_log",
        audit_tables=audit_tables,
        audit_logs=audit_logs,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total_logs,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
    )


@bp.post("/audit-log")
def update_audit_log_settings():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    refresh_field_catalog()
    table_name = request.form.get("table_name", "").strip()
    page = request.form.get("page", "").strip()
    per_page = request.form.get("per_page", "").strip()
    redirect_params = {}
    if page:
        redirect_params["page"] = page
    if per_page:
        redirect_params["per_page"] = per_page
    if not table_name:
        flash("missing table name", "warning")
        return redirect(url_for("admin.audit_log", **redirect_params))

    field_catalog = list_audit_catalog()
    catalog_map = _catalog_map(
        [row for row in field_catalog if row["field_name"] != "__TABLE__"]
    )
    table_fields = catalog_map.get(table_name, set())
    if not table_fields:
        flash("invalid table name", "warning")
        return redirect(url_for("admin.audit_log", **redirect_params))

    selected_fields = request.form.getlist("field_names")
    table_audited = request.form.get("table_audited") == "1"
    logical_fields = _logical_fields_for_table(table_fields)
    if table_audited and len(selected_fields) != len(logical_fields):
        table_audited = False

    if table_audited:
        update_audit_flags(table_name, sorted(table_fields), True)
        update_table_audit_flag(table_name, True)
        detail_fields = ["__TABLE__"]
        message = f"更新审计配置: {table_name} 全表审计"
    else:
        audited_actual_fields = set()
        for logical_name in selected_fields:
            audited_actual_fields.update(_actual_fields(table_fields, logical_name))
        unaudited_fields = set(table_fields) - audited_actual_fields
        update_audit_flags(table_name, sorted(audited_actual_fields), True)
        update_audit_flags(table_name, sorted(unaudited_fields), False)
        update_table_audit_flag(table_name, False)
        detail_fields = {
            "audited": selected_fields,
            "unaudited": sorted(unaudited_fields),
        }
        message = f"更新审计配置: {table_name} 字段"

    current_user = get_current_user()
    create_audit_log(
        None,
        actor="user",
        actor_id=current_user.user_id,
        action_type="update",
        action_detail={
            "table": "field_catalog",
            "op": "update",
            "fields": detail_fields,
            "message": message,
        },
    )
    flash("audit settings updated", "success")
    return redirect(url_for("admin.audit_log", **redirect_params))


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
            actual_fields = _actual_fields(table_fields, field_name)
            if not actual_fields:
                actual_fields = [field_name]
            for actual_field in actual_fields:
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
        actual_fields = []
        for logical_field in field_names:
            for actual_field in _actual_fields(table_fields, logical_field):
                if actual_field in SYSTEM_FIELDS:
                    continue
                actual_fields.append(actual_field)
        if any(
            field_permission_exists(role_id, table_name, actual_field)
            for actual_field in actual_fields
        ):
            flash("field permission already exists", "warning")
            return redirect(url_for("admin.field_permissions"))
        for actual_field in actual_fields:
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


@bp.get("/rental/pricing")
def rental_pricing():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    pricing_rows = list_rental_pricing()
    services = list_rental_services(include_inactive=True)
    pricing_types = [
        "per_booking",
        "per_day",
        "per_hour",
        "per_unit",
    ]
    return render_template(
        "admin/rental_pricing.html",
        active_menu="admin_rental_pricing",
        pricing_rows=pricing_rows,
        services=services,
        pricing_types=pricing_types,
    )


@bp.post("/rental/pricing")
def rental_pricing_actions():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    action = request.form.get("action")
    if action == "pricing_update":
        vehicle_id = _parse_int(request.form.get("vehicle_id"))
        if vehicle_id:
            currency = (request.form.get("currency") or "JPY").strip() or "JPY"
            daily_price = _parse_int(request.form.get("daily_price"), 0) or 0
            deposit_amount = _parse_int(request.form.get("deposit_amount"), 0) or 0
            insurance_per_day = _parse_int(request.form.get("insurance_per_day"), 0) or 0
            free_km_per_day = _parse_int(request.form.get("free_km_per_day"))
            extra_km_price = _parse_int(request.form.get("extra_km_price"))
            cleaning_fee = _parse_int(request.form.get("cleaning_fee"), 0) or 0
            late_fee_per_day = _parse_int(request.form.get("late_fee_per_day"), 0) or 0
            tax_rate = _parse_float(request.form.get("tax_rate"), 10.00) or 10.00
            current_user = get_current_user()
            upsert_rental_pricing(
                vehicle_id=vehicle_id,
                currency=currency,
                daily_price=daily_price,
                deposit_amount=deposit_amount,
                insurance_per_day=insurance_per_day,
                free_km_per_day=free_km_per_day,
                extra_km_price=extra_km_price,
                cleaning_fee=cleaning_fee,
                late_fee_per_day=late_fee_per_day,
                tax_rate=tax_rate,
                updated_by=current_user.user_id,
            )
            flash("rental pricing updated", "success")
    elif action == "service_create":
        code = (request.form.get("code") or "").strip()
        name_jp = (request.form.get("name_jp") or "").strip()
        name_cn = (request.form.get("name_cn") or "").strip()
        pricing_type = (request.form.get("pricing_type") or "").strip()
        price = _parse_int(request.form.get("price"), 0) or 0
        currency = (request.form.get("currency") or "JPY").strip() or "JPY"
        is_active = request.form.get("is_active") == "1"
        if code and name_jp and name_cn and pricing_type:
            create_rental_service(code, name_jp, name_cn, pricing_type, price, currency, is_active)
            flash("rental service created", "success")
        else:
            flash("missing required service fields", "warning")
    elif action == "service_update":
        service_id = _parse_int(request.form.get("service_id"))
        if service_id:
            code = (request.form.get("code") or "").strip()
            name_jp = (request.form.get("name_jp") or "").strip()
            name_cn = (request.form.get("name_cn") or "").strip()
            pricing_type = (request.form.get("pricing_type") or "").strip()
            price = _parse_int(request.form.get("price"), 0) or 0
            currency = (request.form.get("currency") or "JPY").strip() or "JPY"
            is_active = request.form.get("is_active") == "1"
            update_rental_service(
                service_id,
                code,
                name_jp,
                name_cn,
                pricing_type,
                price,
                currency,
                is_active,
            )
            flash("rental service updated", "success")
    return redirect(url_for("admin.rental_pricing", lang=request.args.get("lang")))


@bp.get("/rental/requests")
def rental_requests():
    if not _require_admin():
        return redirect(url_for("ui.dashboard"))
    lang = request.args.get("lang") or "jp"
    requests = list_rental_requests()
    service_rows = list_rental_services(include_inactive=True)
    service_lookup = {
        row["id"]: (row.get("name_jp"), row.get("name_cn")) for row in service_rows
    }
    for row in requests:
        raw_ids = row.get("service_ids")
        service_names = []
        if raw_ids:
            try:
                ids = json.loads(raw_ids) if isinstance(raw_ids, str) else raw_ids
            except (TypeError, ValueError):
                ids = []
            if isinstance(ids, list):
                for service_id in ids:
                    names = service_lookup.get(service_id)
                    if not names:
                        continue
                    service_names.append(names[0] if lang == "jp" else names[1])
        row["service_names"] = service_names
    return render_template(
        "admin/rental_requests.html",
        active_menu="admin_rental_requests",
        rental_requests=requests,
    )
