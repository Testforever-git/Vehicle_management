# app/blueprints/ui/routes.py
import os
import shutil

import yaml

from flask import render_template, redirect, url_for, abort, request, flash, send_from_directory, session
from . import bp
from ...i18n import Translator
from ...security.users import get_current_user
from ...security.permissions import PermissionService
from ...utils.masking import mask_plate
from ...repositories.vehicle_repo import (
    list_vehicles,
    get_vehicle,
    get_vehicle_i18n,
    get_vehicle_by_vin,
    get_status,
    update_vehicle,
    create_vehicle,
    delete_vehicles,
    upsert_status,
)
from ...repositories.master_data_repo import (
    list_brands,
    list_models,
    list_colors,
    list_enums,
)
from ...repositories.vehicle_media_repo import (
    list_vehicle_media,
    create_vehicle_media,
    delete_vehicle_media,
    update_vehicle_media_paths,
    set_primary_vehicle_media,
)
from ...repositories.vehicle_log_repo import log_vehicle_action
from ...repositories.qr_repo import ensure_vehicle_qr, get_vehicle_qr_by_vehicle_id

def _require_login():
    u = get_current_user()
    return u.is_authenticated


VEHICLE_FIELDS = [
    {"name": "vin", "label_key": "vehicle_edit.fields.vin", "type": "text"},
    {"name": "plate_no", "label_key": "vehicle_edit.fields.plate_no", "type": "text"},
    {"name": "brand_id", "label_key": "vehicle_edit.fields.brand_id", "type": "select", "options_key": "brands"},
    {"name": "model_id", "label_key": "vehicle_edit.fields.model_id", "type": "select", "options_key": "models"},
    {"name": "color_id", "label_key": "vehicle_edit.fields.color_id", "type": "select", "options_key": "colors"},
    {"name": "model_year_ad", "label_key": "vehicle_edit.fields.model_year_ad", "type": "number"},
    {"name": "type_designation_code", "label_key": "vehicle_edit.fields.type_designation_code", "type": "text"},
    {"name": "classification_number", "label_key": "vehicle_edit.fields.classification_number", "type": "text"},
    {"name": "engine_code", "label_key": "vehicle_edit.fields.engine_code", "type": "text"},
    {"name": "engine_layout_code", "label_key": "vehicle_edit.fields.engine_layout_code", "type": "select", "options_key": "engine_layout"},
    {"name": "displacement_cc", "label_key": "vehicle_edit.fields.displacement_cc", "type": "number"},
    {"name": "fuel_type_code", "label_key": "vehicle_edit.fields.fuel_type_code", "type": "select", "options_key": "fuel_type"},
    {"name": "drive_type_code", "label_key": "vehicle_edit.fields.drive_type_code", "type": "select", "options_key": "drive_type"},
    {"name": "transmission", "label_key": "vehicle_edit.fields.transmission", "type": "text"},
    {"name": "ownership_type", "label_key": "vehicle_edit.fields.ownership_type", "type": "text"},
    {"name": "owner_id", "label_key": "vehicle_edit.fields.owner_id", "type": "text"},
    {"name": "driver_id", "label_key": "vehicle_edit.fields.driver_id", "type": "text"},
    {"name": "garage_name", "label_key": "vehicle_edit.fields.garage_name", "type": "text"},
    {"name": "garage_address_jp", "label_key": "vehicle_edit.fields.garage_address_jp", "type": "text"},
    {"name": "garage_address_cn", "label_key": "vehicle_edit.fields.garage_address_cn", "type": "text"},
    {"name": "garage_postcode", "label_key": "vehicle_edit.fields.garage_postcode", "type": "text"},
    {"name": "garage_lat", "label_key": "vehicle_edit.fields.garage_lat", "type": "text"},
    {"name": "garage_lng", "label_key": "vehicle_edit.fields.garage_lng", "type": "text"},
    {"name": "purchase_date", "label_key": "vehicle_edit.fields.purchase_date", "type": "date"},
    {"name": "purchase_price", "label_key": "vehicle_edit.fields.purchase_price", "type": "number"},
    {"name": "note", "label_key": "vehicle_edit.fields.note", "type": "textarea"},
]

NULLABLE_NUMERIC_FIELDS = {
    "owner_id",
    "driver_id",
    "garage_lat",
    "garage_lng",
    "brand_id",
    "model_id",
    "color_id",
    "model_year_ad",
    "displacement_cc",
    "purchase_price",
}

NULLABLE_TEXT_FIELDS = {
    "note",
}

PHOTO_FILE_TYPE = "photo"
PHOTO_DIR_CATEGORY = "vehicle_photo"
LEGACY_PHOTO_DIR_CATEGORY = "Vehicle_photo"

_translator = Translator()
_YEAR_CONVERSION_CACHE = None


def _image_base_dir():
    return os.path.join(os.getcwd(), "db", "image")


def _load_year_conversion():
    global _YEAR_CONVERSION_CACHE
    if _YEAR_CONVERSION_CACHE is not None:
        return _YEAR_CONVERSION_CACHE
    conversion_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "static",
        "i18n",
        "convert_year.yaml",
    )
    try:
        with open(conversion_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    ad_to_era = {}
    era_to_ad = {}
    for ad_year, era_year in data.items():
        if not isinstance(ad_year, str) or not isinstance(era_year, str):
            continue
        ad_clean = ad_year.strip()
        if ad_clean.endswith("年"):
            ad_clean = ad_clean[:-1]
        era_clean = era_year.strip()
        ad_to_era[ad_clean] = era_clean
        era_to_ad[era_clean] = ad_clean
    _YEAR_CONVERSION_CACHE = {"ad_to_era": ad_to_era, "era_to_ad": era_to_ad}
    return _YEAR_CONVERSION_CACHE


def _safe_vin(vin: str) -> str:
    return "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in vin])


def _vehicle_image_dirs(vin: str):
    safe_vin = _safe_vin(vin)
    legal_dir = os.path.join(_image_base_dir(), safe_vin, "legal_doc")
    photo_dir = os.path.join(_image_base_dir(), safe_vin, PHOTO_DIR_CATEGORY)
    legacy_photo_dir = os.path.join(_image_base_dir(), safe_vin, LEGACY_PHOTO_DIR_CATEGORY)
    if os.path.exists(legacy_photo_dir) and not os.path.exists(photo_dir):
        photo_dir = legacy_photo_dir
    return legal_dir, photo_dir


def _save_uploads(files, target_dir):
    saved = []
    if not files:
        return saved
    os.makedirs(target_dir, exist_ok=True)
    for f in files:
        if not f or not f.filename:
            continue
        name = os.path.basename(f.filename)
        file_path = os.path.join(target_dir, name)
        f.save(file_path)
        saved.append(name)
    return saved


def _remove_files(target_dir, filenames):
    for name in filenames:
        if not name:
            continue
        file_path = os.path.join(target_dir, os.path.basename(name))
        if os.path.exists(file_path):
            os.remove(file_path)


def _payload_from_form():
    payload = {}
    for field in VEHICLE_FIELDS:
        name = field["name"]
        if name in request.form:
            value = request.form.get(name)
            if isinstance(value, str):
                value = value.strip()
            if value == "" and (
                field.get("type") in {"number", "date"}
                or name in NULLABLE_NUMERIC_FIELDS
                or name in NULLABLE_TEXT_FIELDS
            ):
                payload[name] = None
            else:
                payload[name] = value
    return payload


STATUS_FIELDS = [
    {"name": "status", "label_key": "vehicle_status.fields.status", "type": "select", "options_key": "status_options"},
    {"name": "mileage", "label_key": "vehicle_status.fields.mileage", "type": "number"},
    {"name": "fuel_level", "label_key": "vehicle_status.fields.fuel_level", "type": "number"},
    {"name": "location_desc", "label_key": "vehicle_status.fields.location_desc", "type": "text"},
]


def _status_payload_from_form():
    payload = {}
    for field in STATUS_FIELDS:
        name = field["name"]
        if name in request.form:
            value = request.form.get(name)
            if isinstance(value, str):
                value = value.strip()
            if value == "" and field.get("type") in {"number"}:
                payload[name] = None
            else:
                payload[name] = value
    return payload


def _load_master_data():
    brands = list_brands()
    models = list_models()
    colors = list_colors()
    enums = list_enums()

    brand_options = [
        {
            "value": row["id"],
            "label": f"{row['name_jp']} / {row['name_cn']}",
            "is_active": bool(row.get("is_active", 1)),
        }
        for row in brands
    ]
    brand_map = {row["id"]: row for row in brands}
    model_options = []
    for row in models:
        brand = brand_map.get(row["brand_id"])
        brand_label = f"{brand['name_jp']} / {brand['name_cn']}" if brand else "-"
        model_label = f"{row['name_jp']} / {row['name_cn']}"
        model_options.append(
            {
                "value": row["id"],
                "label": f"{brand_label} - {model_label}",
                "is_active": bool(row.get("is_active", 1)),
                "brand_id": row["brand_id"],
            }
        )

    color_options = [
        {
            "value": row["id"],
            "label": f"{row['name_jp']} / {row['name_cn']}",
            "is_active": bool(row.get("is_active", 1)),
        }
        for row in colors
    ]
    enum_groups = {}
    for row in enums:
        enum_groups.setdefault(row["enum_type"], []).append(
            {
                "value": row["enum_code"],
                "label": f"{row['name_jp']} / {row['name_cn']}",
                "is_active": bool(row.get("is_active", 1)),
            }
        )

    return {
        "brands": brand_options,
        "models": model_options,
        "colors": color_options,
        "engine_layout": enum_groups.get("engine_layout", []),
        "fuel_type": enum_groups.get("fuel_type", []),
        "drive_type": enum_groups.get("drive_type", []),
        "status_options": [
            {"value": "available", "label": "available", "is_active": True},
            {"value": "rented", "label": "rented", "is_active": True},
            {"value": "maintenance", "label": "maintenance", "is_active": True},
        ],
    }


def _media_rel_paths(vin: str, category: str, filenames: list[str]) -> list[str]:
    base_dir = _image_base_dir()
    safe_vin = _safe_vin(vin)
    rel_paths = []
    for name in filenames:
        if not name:
            continue
        rel_paths.append(os.path.relpath(os.path.join(base_dir, safe_vin, category, name), base_dir))
    return rel_paths


def _media_filenames(rows: list[dict]) -> list[str]:
    return [os.path.basename(row.get("file_path", "")) for row in rows if row.get("file_path")]


def _media_items(rows: list[dict]) -> list[dict]:
    items = []
    for row in rows:
        file_path = row.get("file_path")
        if not file_path:
            continue
        items.append(
            {
                "filename": os.path.basename(file_path),
                "is_primary": bool(row.get("is_primary")) if "is_primary" in row else False,
                "file_path": file_path,
            }
        )
    return items


def _t(key: str) -> str:
    lang = request.args.get("lang") or session.get("lang") or "jp"
    return _translator.t(lang, key)


@bp.get("/vehicle/image/<vin>/<category>/<filename>")
def vehicle_image(vin: str, category: str, filename: str):
    if not _require_login():
        return redirect(url_for("auth.login"))
    if category not in {"legal_doc", PHOTO_DIR_CATEGORY, LEGACY_PHOTO_DIR_CATEGORY}:
        abort(404)
    safe_vin = _safe_vin(vin)
    base_dir = _image_base_dir()
    if category == "legal_doc":
        dir_path = os.path.join(base_dir, safe_vin, category)
    else:
        candidate_dirs = [
            os.path.join(base_dir, safe_vin, PHOTO_DIR_CATEGORY),
            os.path.join(base_dir, safe_vin, LEGACY_PHOTO_DIR_CATEGORY),
        ]
        dir_path = candidate_dirs[0]
        for candidate in candidate_dirs:
            if os.path.exists(os.path.join(candidate, filename)):
                dir_path = candidate
                break
    return send_from_directory(dir_path, filename)


@bp.get("/dashboard")
def dashboard():
    if not _require_login():
        return redirect(url_for("auth.login"))
    _, total = list_vehicles()
    return render_template("dashboard.html", active_menu="dashboard", total=total)


@bp.route("/vehicle/list", methods=["GET", "POST"])
def vehicle_list():
    if not _require_login():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        perms = PermissionService(get_current_user())
        if not perms.can("vehicle", "edit"):
            flash(_t("vehicle_list.messages.no_permission"), "warning")
            return redirect(url_for("ui.vehicle_list", lang=request.args.get("lang")))
        action = request.form.get("action")
        ids = [int(v) for v in request.form.getlist("vehicle_ids") if v.isdigit()]
        if action == "delete" and ids:
            delete_vehicles(ids)
            flash(_t("vehicle_list.messages.deleted"), "success")
        return redirect(url_for("ui.vehicle_list", lang=request.args.get("lang")))

    brand = request.args.get("brand", "").strip()
    status = request.args.get("status", "").strip()
    try:
        page = int(request.args.get("page", "1") or 1)
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", "20") or 20)
    except ValueError:
        per_page = 20
    if per_page not in {20, 50}:
        per_page = 20
    if page < 1:
        page = 1

    rows, total = list_vehicles(
        filters={"brand": brand, "status": status},
        page=page,
        per_page=per_page,
    )
    vehicles = []
    for v in rows:
        vv = dict(v)
        vv["masked_plate_no"] = mask_plate(v.get("plate_no", ""))
        if vv.get("status") is None:
            vv["status"] = "unknown"
        vehicles.append(vv)

    status_options = [("available", "available"), ("rented", "rented"), ("maintenance", "maintenance")]
    total_pages = max((total + per_page - 1) // per_page, 1)

    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }

    return render_template(
        "vehicle/list.html",
        active_menu="vehicle",
        vehicles=vehicles,
        pagination=pagination,
        status_options=status_options,
        filters={"brand": brand, "status": status},
    )

@bp.get("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))

    vehicle = get_vehicle_i18n(vehicle_id)
    if not vehicle:
        abort(404)

    vehicle_vm = dict(vehicle)
    vehicle_vm["masked_plate_no"] = mask_plate(vehicle.get("plate_no", ""))

    status = None
    try:
        status = get_status(vehicle_id)
    except Exception:
        status = None

    legal_docs = _media_filenames(list_vehicle_media(vehicle_id, "legal_doc"))
    vehicle_photos = _media_filenames(list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE))
    qr_row = get_vehicle_qr_by_vehicle_id(vehicle_id)

    return render_template(
        "vehicle/detail.html",
        active_menu="vehicle",
        vehicle=vehicle_vm,
        status=status,
        recent_logs=[],
        legal_docs=legal_docs,
        vehicle_photos=vehicle_photos,
        qr_slug=qr_row["qr_slug"] if qr_row else None,
    )

@bp.route("/vehicle/<int:vehicle_id>/edit", methods=["GET","POST"])
def vehicle_edit(vehicle_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))

    vehicle = get_vehicle(vehicle_id)
    if not vehicle:
        abort(404)

    if request.method == "POST":
        payload = _payload_from_form()
        status_payload = _status_payload_from_form()
        vin = (payload.get("vin") or vehicle.get("vin") or "").strip()
        if not vin:
            flash(_t("vehicle_edit.messages.vin_required"), "warning")
            return redirect(url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")))

        existing = get_vehicle_by_vin(vin)
        if existing and existing["id"] != vehicle_id:
            flash(_t("vehicle_edit.messages.vin_exists"), "warning")
            return redirect(url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")))

        legal_dir, photo_dir = _vehicle_image_dirs(vin)
        if vehicle.get("vin") and vehicle.get("vin") != vin:
            old_legal_dir, old_photo_dir = _vehicle_image_dirs(vehicle["vin"])
            if os.path.exists(old_legal_dir):
                os.makedirs(os.path.dirname(legal_dir), exist_ok=True)
                shutil.move(old_legal_dir, legal_dir)
            if os.path.exists(old_photo_dir):
                os.makedirs(os.path.dirname(photo_dir), exist_ok=True)
                shutil.move(old_photo_dir, photo_dir)
            update_vehicle_media_paths(
                vehicle_id,
                f"{_safe_vin(vehicle['vin'])}/",
                f"{_safe_vin(vin)}/",
            )

        removed_legal = request.form.get("remove_legal_docs", "").split(",")
        removed_photos = request.form.get("remove_vehicle_photos", "").split(",")

        _remove_files(legal_dir, removed_legal)
        _remove_files(photo_dir, removed_photos)

        delete_vehicle_media(
            vehicle_id,
            "legal_doc",
            _media_rel_paths(vin, "legal_doc", removed_legal),
        )
        delete_vehicle_media(
            vehicle_id,
            PHOTO_FILE_TYPE,
            _media_rel_paths(vin, PHOTO_DIR_CATEGORY, removed_photos)
            + _media_rel_paths(vin, LEGACY_PHOTO_DIR_CATEGORY, removed_photos),
        )

        new_legal = _save_uploads(request.files.getlist("legal_doc_files"), legal_dir)
        new_photos = _save_uploads(request.files.getlist("vehicle_photo_files"), photo_dir)

        create_vehicle_media(
            vehicle_id,
            "legal_doc",
            _media_rel_paths(vin, "legal_doc", new_legal),
            get_current_user().user_id,
        )
        create_vehicle_media(
            vehicle_id,
            PHOTO_FILE_TYPE,
            _media_rel_paths(vin, PHOTO_DIR_CATEGORY, new_photos),
            get_current_user().user_id,
        )
        primary_photo = (request.form.get("primary_vehicle_photo") or "").strip()
        if primary_photo:
            photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
            primary_row = next(
                (row for row in photo_rows if os.path.basename(row.get("file_path", "")) == primary_photo),
                None,
            )
            if primary_row:
                set_primary_vehicle_media(vehicle_id, PHOTO_FILE_TYPE, primary_row["file_path"])

        payload["updated_by"] = get_current_user().user_id
        update_vehicle(vehicle_id, payload)
        ensure_vehicle_qr(vehicle_id)
        if status_payload:
            status_payload["updated_by"] = get_current_user().user_id
            upsert_status(vehicle_id, status_payload)
        log_vehicle_action(
            vehicle_id,
            actor=get_current_user().username,
            action_type="vehicle_update",
            action_detail={
                "vin": vin,
                "removed_legal": [f for f in removed_legal if f],
                "removed_photos": [f for f in removed_photos if f],
                "new_legal": new_legal,
                "new_photos": new_photos,
            },
            source_module="vehicle_edit",
        )
        return redirect(url_for("ui.vehicle_detail", vehicle_id=vehicle_id, lang=request.args.get("lang")))

    legal_docs = _media_filenames(list_vehicle_media(vehicle_id, "legal_doc"))
    photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
    vehicle_photos = _media_items(photo_rows)
    has_primary_photo = any(item["is_primary"] for item in vehicle_photos)
    status = get_status(vehicle_id) or {}
    master_data = _load_master_data()

    return render_template(
        "vehicle/edit.html",
        active_menu="vehicle",
        vehicle=vehicle,
        vehicle_fields=VEHICLE_FIELDS,
        status_fields=STATUS_FIELDS,
        status_data=status,
        master_data=master_data,
        year_conversion=_load_year_conversion(),
        legal_docs=legal_docs,
        vehicle_photos=vehicle_photos,
        has_primary_photo=has_primary_photo,
        form_action=url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")),
        cancel_url=url_for("ui.vehicle_detail", vehicle_id=vehicle_id, lang=request.args.get("lang")),
        is_new=False,
    )


@bp.route("/vehicle/new", methods=["GET", "POST"])
def vehicle_new():
    if not _require_login():
        return redirect(url_for("auth.login"))

    source_id = request.args.get("source_id")
    vehicle = {field["name"]: "" for field in VEHICLE_FIELDS}
    if source_id:
        source_vehicle = get_vehicle(int(source_id))
        if source_vehicle:
            for field in VEHICLE_FIELDS:
                vehicle[field["name"]] = source_vehicle.get(field["name"], "")
            vehicle["vin"] = ""

    if request.method == "POST":
        payload = _payload_from_form()
        status_payload = _status_payload_from_form()
        vin = (payload.get("vin") or "").strip()
        if not vin:
            flash(_t("vehicle_edit.messages.vin_required"), "warning")
            return redirect(url_for("ui.vehicle_new", lang=request.args.get("lang")))
        if get_vehicle_by_vin(vin):
            flash(_t("vehicle_edit.messages.vin_exists"), "warning")
            return redirect(url_for("ui.vehicle_new", lang=request.args.get("lang")))

        legal_dir, photo_dir = _vehicle_image_dirs(vin)
        new_legal = _save_uploads(request.files.getlist("legal_doc_files"), legal_dir)
        new_photos = _save_uploads(request.files.getlist("vehicle_photo_files"), photo_dir)

        payload["updated_by"] = get_current_user().user_id
        create_vehicle(payload)
        created = get_vehicle_by_vin(vin)
        if created:
            ensure_vehicle_qr(created["id"])
            if status_payload:
                status_payload["updated_by"] = get_current_user().user_id
                upsert_status(created["id"], status_payload)
            create_vehicle_media(
                created["id"],
                "legal_doc",
                _media_rel_paths(vin, "legal_doc", new_legal),
                get_current_user().user_id,
            )
            create_vehicle_media(
                created["id"],
                PHOTO_FILE_TYPE,
                _media_rel_paths(vin, PHOTO_DIR_CATEGORY, new_photos),
                get_current_user().user_id,
            )
            log_vehicle_action(
                created["id"],
                actor=get_current_user().username,
                action_type="vehicle_create",
                action_detail={"vin": vin, "legal": new_legal, "photos": new_photos},
                source_module="vehicle_new",
            )
            return redirect(url_for("ui.vehicle_detail", vehicle_id=created["id"], lang=request.args.get("lang")))
        return redirect(url_for("ui.vehicle_list", lang=request.args.get("lang")))

    return render_template(
        "vehicle/edit.html",
        active_menu="vehicle",
        vehicle=vehicle,
        vehicle_fields=VEHICLE_FIELDS,
        status_fields=STATUS_FIELDS,
        status_data={},
        master_data=_load_master_data(),
        year_conversion=_load_year_conversion(),
        legal_docs=[],
        vehicle_photos=[],
        has_primary_photo=False,
        form_action=url_for("ui.vehicle_new", lang=request.args.get("lang")),
        cancel_url=url_for("ui.vehicle_list", lang=request.args.get("lang")),
        is_new=True,
    )
