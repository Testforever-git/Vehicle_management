# app/blueprints/ui/routes.py
import json
import os
import shutil

from flask import render_template, redirect, url_for, abort, request, flash, send_from_directory
from . import bp
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

def _require_login():
    u = get_current_user()
    return u.is_authenticated


VEHICLE_FIELDS = [
    {"name": "vin", "label": "VIN", "type": "text"},
    {"name": "plate_no", "label": "Plate No", "type": "text"},
    {"name": "brand_cn", "label": "Brand (CN)", "type": "text"},
    {"name": "brand_jp", "label": "Brand (JP)", "type": "text"},
    {"name": "model_cn", "label": "Model (CN)", "type": "text"},
    {"name": "model_jp", "label": "Model (JP)", "type": "text"},
    {"name": "color_cn", "label": "Color (CN)", "type": "text"},
    {"name": "color_jp", "label": "Color (JP)", "type": "text"},
    {"name": "model_year", "label": "Model Year", "type": "number"},
    {"name": "type_designation_code", "label": "Type Designation Code", "type": "text"},
    {"name": "classification_number", "label": "Classification Number", "type": "text"},
    {"name": "engine_code", "label": "Engine Code", "type": "text"},
    {"name": "engine_layout", "label": "Engine Layout", "type": "text"},
    {"name": "displacement_cc", "label": "Displacement (cc)", "type": "number"},
    {"name": "fuel_type", "label": "Fuel Type", "type": "text"},
    {"name": "drive_type", "label": "Drive Type", "type": "text"},
    {"name": "transmission", "label": "Transmission", "type": "text"},
    {"name": "ownership_type", "label": "Ownership Type", "type": "text"},
    {"name": "owner_id", "label": "Owner ID", "type": "text"},
    {"name": "driver_id", "label": "Driver ID", "type": "text"},
    {"name": "garage_name", "label": "Garage Name", "type": "text"},
    {"name": "garage_address_jp", "label": "Garage Address (JP)", "type": "text"},
    {"name": "garage_address_cn", "label": "Garage Address (CN)", "type": "text"},
    {"name": "garage_postcode", "label": "Garage Postcode", "type": "text"},
    {"name": "garage_lat", "label": "Garage Lat", "type": "text"},
    {"name": "garage_lng", "label": "Garage Lng", "type": "text"},
    {"name": "purchase_date", "label": "Purchase Date", "type": "date"},
    {"name": "purchase_price", "label": "Purchase Price", "type": "number"},
    {"name": "ext_json", "label": "Extra JSON", "type": "textarea"},
    {"name": "note", "label": "Note", "type": "textarea"},
]


def _image_base_dir():
    return os.path.join(os.getcwd(), "db", "image")


def _safe_vin(vin: str) -> str:
    return "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in vin])


def _vehicle_image_dirs(vin: str):
    safe_vin = _safe_vin(vin)
    legal_dir = os.path.join(_image_base_dir(), safe_vin, "legal_doc")
    photo_dir = os.path.join(_image_base_dir(), safe_vin, "Vehicle_photo")
    return legal_dir, photo_dir


def _parse_image_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return [v for v in str(value).split(",") if v]


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
            payload[name] = request.form.get(name)
    return payload


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

    return render_template(
        "vehicle/detail.html",
        active_menu="vehicle",
        vehicle=vehicle_vm,
        status=status,
        recent_logs=[],
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
        vin = (payload.get("vin") or "").strip()
        if not vin:
            flash("VIN is required", "warning")
            return redirect(url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")))

        existing = get_vehicle_by_vin(vin)
        if existing and existing["id"] != vehicle_id:
            flash("VIN already exists", "warning")
            return redirect(url_for("ui.vehicle_edit", vehicle_id=vehicle_id, lang=request.args.get("lang")))

        legal_dir, photo_dir = _vehicle_image_dirs(vin)
        payload["legal_doc_dir"] = os.path.relpath(legal_dir, os.getcwd())
        payload["vehicle_photo_dir"] = os.path.relpath(photo_dir, os.getcwd())

        current_legal = _parse_image_list(vehicle.get("legal_doc"))
        current_photos = _parse_image_list(vehicle.get("vehicle_photo"))

        removed_legal = request.form.get("remove_legal_docs", "").split(",")
        removed_photos = request.form.get("remove_vehicle_photos", "").split(",")

        _remove_files(legal_dir, removed_legal)
        _remove_files(photo_dir, removed_photos)

        updated_legal = [f for f in current_legal if f not in removed_legal]
        updated_photos = [f for f in current_photos if f not in removed_photos]

        new_legal = _save_uploads(request.files.getlist("legal_doc_files"), legal_dir)
        new_photos = _save_uploads(request.files.getlist("vehicle_photo_files"), photo_dir)

        payload["legal_doc"] = json.dumps(updated_legal + new_legal)
        payload["vehicle_photo"] = json.dumps(updated_photos + new_photos)

        if vehicle.get("vin") and vehicle.get("vin") != vin:
            old_legal_dir, old_photo_dir = _vehicle_image_dirs(vehicle["vin"])
            if os.path.exists(old_legal_dir):
                os.makedirs(os.path.dirname(legal_dir), exist_ok=True)
                shutil.move(old_legal_dir, legal_dir)
            if os.path.exists(old_photo_dir):
                os.makedirs(os.path.dirname(photo_dir), exist_ok=True)
                shutil.move(old_photo_dir, photo_dir)

        update_vehicle(vehicle_id, payload)
        return redirect(url_for("ui.vehicle_detail", vehicle_id=vehicle_id, lang=request.args.get("lang")))

    legal_docs = _parse_image_list(vehicle.get("legal_doc"))
    vehicle_photos = _parse_image_list(vehicle.get("vehicle_photo"))

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
            vehicle["legal_doc"] = ""
            vehicle["vehicle_photo"] = ""

    if request.method == "POST":
        payload = _payload_from_form()
        vin = (payload.get("vin") or "").strip()
        if not vin:
            flash("VIN is required", "warning")
            return redirect(url_for("ui.vehicle_new", lang=request.args.get("lang")))
        if get_vehicle_by_vin(vin):
            flash("VIN already exists", "warning")
            return redirect(url_for("ui.vehicle_new", lang=request.args.get("lang")))

        legal_dir, photo_dir = _vehicle_image_dirs(vin)
        payload["legal_doc_dir"] = os.path.relpath(legal_dir, os.getcwd())
        payload["vehicle_photo_dir"] = os.path.relpath(photo_dir, os.getcwd())

        new_legal = _save_uploads(request.files.getlist("legal_doc_files"), legal_dir)
        new_photos = _save_uploads(request.files.getlist("vehicle_photo_files"), photo_dir)

        payload["legal_doc"] = json.dumps(new_legal)
        payload["vehicle_photo"] = json.dumps(new_photos)

        create_vehicle(payload)
        created = get_vehicle_by_vin(vin)
        if created:
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
