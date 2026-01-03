# app/blueprints/portal/routes.py
import os

from flask import render_template, abort, send_from_directory, redirect, url_for, request

from . import bp
from ...repositories.vehicle_repo import list_vehicles, get_vehicle_i18n, get_status
from ...repositories.vehicle_media_repo import list_vehicle_media
from ...repositories.customer_repo import get_customer_by_identity
from ...security.customers import get_current_customer, login_customer

PHOTO_FILE_TYPE = "photo"
PHOTO_DIR_CATEGORY = "vehicle_photo"
LEGACY_PHOTO_DIR_CATEGORY = "Vehicle_photo"



def _image_base_dir():
    return os.path.join(os.getcwd(), "db", "image")


def _safe_vin(vin: str) -> str:
    return "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in vin])


def _select_cover_filename(rows: list[dict]) -> str | None:
    for row in rows:
        if row.get("is_primary"):
            return os.path.basename(row.get("file_path", ""))
    if rows:
        return os.path.basename(rows[0].get("file_path", ""))
    return None


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


def _build_public_vehicle_card(vehicle_row: dict) -> dict:
    vehicle_id = vehicle_row["id"]
    photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
    cover_filename = _select_cover_filename(photo_rows)
    status = get_status(vehicle_id) or {}
    return {
        "id": vehicle_id,
        "vin": vehicle_row.get("vin"),
        "brand_cn": vehicle_row.get("brand_cn"),
        "brand_jp": vehicle_row.get("brand_jp"),
        "model_cn": vehicle_row.get("model_cn"),
        "model_jp": vehicle_row.get("model_jp"),
        "mileage": status.get("mileage"),
        "cover_filename": cover_filename,
    }


@bp.get("/")
def portal_root():
    return render_template("portal/home.html", active_menu="portal")


@bp.get("/portal")
def portal_home():
    return render_template("portal/home.html", active_menu="portal")


@bp.get("/portal/repair")
def portal_repair():
    return render_template("portal/repair.html", active_menu="portal")


@bp.get("/portal/trade")
def portal_trade():
    return render_template("portal/trade.html", active_menu="portal")


@bp.get("/portal/rentals")
def portal_rentals():
    vehicles, _ = list_vehicles(page=1, per_page=500)
    cards = [_build_public_vehicle_card(row) for row in vehicles]
    return render_template("portal/rentals.html", active_menu="portal", vehicles=cards)


@bp.get("/portal/repair/apply")
def portal_repair_apply():
    customer = get_current_customer()
    if not customer.is_authenticated:
        return redirect(url_for("portal.portal_customer_login", next="portal.portal_repair_apply", lang=request.args.get("lang")))
    return render_template("portal/repair_apply.html", active_menu="portal")


@bp.get("/portal/rentals/apply")
def portal_rentals_apply():
    customer = get_current_customer()
    if not customer.is_authenticated:
        return redirect(url_for("portal.portal_customer_login", next="portal.portal_rentals_apply", lang=request.args.get("lang")))
    return render_template("portal/rental_apply.html", active_menu="portal")


@bp.get("/portal/trade/apply")
def portal_trade_apply():
    customer = get_current_customer()
    if not customer.is_authenticated:
        return redirect(url_for("portal.portal_customer_login", next="portal.portal_trade_apply", lang=request.args.get("lang")))
    return render_template("portal/trade_apply.html", active_menu="portal")


@bp.get("/portal/price-apply")
def portal_price_apply():
    customer = get_current_customer()
    if not customer.is_authenticated:
        return redirect(url_for("portal.portal_customer_login", next="portal.portal_price_apply", lang=request.args.get("lang")))
    return render_template("portal/price_apply.html", active_menu="portal")


@bp.get("/portal/customer-login")
def portal_customer_login():
    return render_template(
        "portal/customer_login.html",
        active_menu="portal",
        next_endpoint=request.args.get("next") or "portal.portal_home",
    )


@bp.post("/portal/customer-login")
def portal_customer_login_post():
    identifier = request.form.get("identifier", "").strip()
    next_endpoint = request.form.get("next") or "portal.portal_home"
    if not identifier:
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            error="missing",
        )
    customer = get_customer_by_identity("email", identifier)
    if not customer or customer.get("status") != "active":
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            error="invalid",
        )
    login_customer(customer["id"])
    return redirect(url_for(next_endpoint, lang=request.args.get("lang")))


@bp.get("/portal/rentals/<int:vehicle_id>")
def portal_rental_detail(vehicle_id: int):
    vehicle = get_vehicle_i18n(vehicle_id)
    if not vehicle:
        abort(404)
    status = get_status(vehicle_id) or {}
    photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
    cover_filename = _select_cover_filename(photo_rows)
    photo_items = _media_items(photo_rows)
    return render_template(
        "portal/rental_detail.html",
        active_menu="portal",
        vehicle=vehicle,
        status=status,
        cover_filename=cover_filename,
        vehicle_photos=photo_items,
    )


@bp.get("/portal/vehicle/image/<vin>/<category>/<filename>")
def portal_vehicle_image(vin: str, category: str, filename: str):
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
