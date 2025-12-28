# app/blueprints/ui/routes.py
import os
import shutil

from flask import render_template, redirect, url_for, abort, request, flash, send_from_directory, session
from . import bp
from ...i18n import Translator
from ...security.users import get_current_user
from ...utils.masking import mask_plate
from ...repositories.vehicle_repo import (
    list_vehicles,
    get_vehicle,
    get_vehicle_by_vin,
    get_status,
    update_vehicle,
    create_vehicle,
)
from ...repositories.vehicle_media_repo import (
    list_vehicle_media,
    create_vehicle_media,
    delete_vehicle_media,
    update_vehicle_media_paths,
)
from ...repositories.vehicle_log_repo import log_vehicle_action

def _require_login():
    u = get_current_user()
    return u.is_authenticated


VEHICLE_FIELDS = [
    {"name": "vin", "label_key": "vehicle_edit.fields.vin", "type": "text"},
    {"name": "plate_no", "label_key": "vehicle_edit.fields.plate_no", "type": "text"},
    {"name": "brand_cn", "label_key": "vehicle_edit.fields.brand_cn", "type": "text"},
    {"name": "brand_jp", "label_key": "vehicle_edit.fields.brand_jp", "type": "text"},
    {"name": "model_cn", "label_key": "vehicle_edit.fields.model_cn", "type": "text"},
    {"name": "model_jp", "label_key": "vehicle_edit.fields.model_jp", "type": "text"},
    {"name": "color_cn", "label_key": "vehicle_edit.fields.color_cn", "type": "text"},
    {"name": "color_jp", "label_key": "vehicle_edit.fields.color_jp", "type": "text"},
    {"name": "model_year", "label_key": "vehicle_edit.fields.model_year", "type": "number"},
    {"name": "type_designation_code", "label_key": "vehicle_edit.fields.type_designation_code", "type": "text"},
    {"name": "classification_number", "label_key": "vehicle_edit.fields.classification_number", "type": "text"},
    {"name": "engine_code", "label_key": "vehicle_edit.fields.engine_code", "type": "text"},
    {"name": "engine_layout", "label_key": "vehicle_edit.fields.engine_layout", "type": "text"},
    {"name": "displacement_cc", "label_key": "vehicle_edit.fields.displacement_cc", "type": "number"},
    {"name": "fuel_type", "label_key": "vehicle_edit.fields.fuel_type", "type": "text"},
    {"name": "drive_type", "label_key": "vehicle_edit.fields.drive_type", "type": "text"},
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
    {"name": "ext_json", "label_key": "vehicle_edit.fields.ext_json", "type": "textarea"},
    {"name": "note", "label_key": "vehicle_edit.fields.note", "type": "textarea"},
]

_translator = Translator()


def _image_base_dir():
    return os.path.join(os.getcwd(), "db", "image")


def _safe_vin(vin: str) -> str:
    return "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in vin])


def _vehicle_image_dirs(vin: str):
    safe_vin = _safe_vin(vin)
    legal_dir = os.path.join(_image_base_dir(), safe_vin, "legal_doc")
    photo_dir = os.path.join(_image_base_dir(), safe_vin, "Vehicle_photo")
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
            if value == "" and field.get("type") in {"number", "date"}:
                payload[name] = None
            else:
                payload[name] = value
    return payload


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

def _t(key: str) -> str:
    lang = request.args.get("lang") or session.get("lang") or "jp"
    return _translator.t(lang, key)


@bp.get("/vehicle/image/<vin>/<category>/<filename>")
def vehicle_image(vin: str, category: str, filename: str):
    if not _require_login():
        return redirect(url_for("auth.login"))
    if category not in {"legal_doc", "Vehicle_photo"}:
        abort(404)
    safe_vin = _safe_vin(vin)
    base_dir = _image_base_dir()
    dir_path = os.path.join(base_dir, safe_vin, category)
    return send_from_directory(dir_path, filename)

@bp.get("/")
def home():
    return redirect(url_for("ui.dashboard"))

@bp.get("/dashboard")
def dashboard():
    if not _require_login():
        return redirect(url_for("auth.login"))
    vehicles = list_vehicles()
    total = len(vehicles)
    return render_template("dashboard.html", active_menu="dashboard", total=total)

@bp.get("/vehicle/list")
def vehicle_list():
    if not _require_login():
        return redirect(url_for("auth.login"))

    rows = list_vehicles()
    vehicles = []
    for v in rows:
        vv = dict(v)
        vv["masked_plate_no"] = mask_plate(v.get("plate_no", ""))
        # status 可选：如果你没建 vehicle_status 表，这里可以先不显示
        try:
            st = get_status(v["id"])
            vv["status"] = st["status"] if st else "unknown"
        except Exception:
            vv["status"] = "unknown"
        vehicles.append(vv)

    status_options = [("available","available"), ("rented","rented"), ("maintenance","maintenance")]

    class P:
        total = len(vehicles)

    return render_template(
        "vehicle/list.html",
        active_menu="vehicle",
        vehicles=vehicles,
        pagination=P(),
        status_options=status_options,
    )

@bp.get("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))

    vehicle = get_vehicle(vehicle_id)
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
    vehicle_photos = _media_filenames(list_vehicle_media(vehicle_id, "vehicle_photo"))

    return render_template(
        "vehicle/detail.html",
        active_menu="vehicle",
        vehicle=vehicle_vm,
        status=status,
        recent_logs=[],
        legal_docs=legal_docs,
        vehicle_photos=vehicle_photos,
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
            "vehicle_photo",
            _media_rel_paths(vin, "Vehicle_photo", removed_photos),
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
            "vehicle_photo",
            _media_rel_paths(vin, "Vehicle_photo", new_photos),
            get_current_user().user_id,
        )

        payload["updated_by"] = get_current_user().user_id
        update_vehicle(vehicle_id, payload)
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
    vehicle_photos = _media_filenames(list_vehicle_media(vehicle_id, "vehicle_photo"))

    return render_template(
        "vehicle/edit.html",
        active_menu="vehicle",
        vehicle=vehicle,
        vehicle_fields=VEHICLE_FIELDS,
        legal_docs=legal_docs,
        vehicle_photos=vehicle_photos,
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
            create_vehicle_media(
                created["id"],
                "legal_doc",
                _media_rel_paths(vin, "legal_doc", new_legal),
                get_current_user().user_id,
            )
            create_vehicle_media(
                created["id"],
                "vehicle_photo",
                _media_rel_paths(vin, "Vehicle_photo", new_photos),
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
        legal_docs=[],
        vehicle_photos=[],
        form_action=url_for("ui.vehicle_new", lang=request.args.get("lang")),
        cancel_url=url_for("ui.vehicle_list", lang=request.args.get("lang")),
        is_new=True,
    )
