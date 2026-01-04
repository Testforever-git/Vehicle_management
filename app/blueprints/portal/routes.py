# app/blueprints/portal/routes.py
import os
import re

from flask import render_template, abort, send_from_directory, redirect, url_for, request, session

from . import bp
from ...repositories.vehicle_repo import list_vehicles, get_vehicle_i18n, get_status
from ...repositories.vehicle_media_repo import list_vehicle_media
from ...repositories.customer_repo import get_customer_by_identity, update_customer_last_login
from ...repositories.rental_pricing_repo import get_rental_pricing, list_rental_pricing_for_vehicle_ids
from ...repositories.rental_service_repo import list_rental_services
from ...repositories.rental_booking_repo import create_rental_booking, get_booking_by_token
from ...repositories.rental_delivery_fee_repo import list_delivery_fee_tiers
from ...repositories.store_repo import list_stores, get_store
from ...security.customers import get_current_customer, login_customer, logout_customer
from ...security.users import get_current_user
import secrets
import json
import math
from datetime import datetime

PHOTO_FILE_TYPE = "photo"
PHOTO_DIR_CATEGORY = "vehicle_photo"
LEGACY_PHOTO_DIR_CATEGORY = "Vehicle_photo"
DEFAULT_CUSTOMER_CODE = "123321"



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


def _detect_identity(identifier: str) -> tuple[str | None, str | None]:
    if not identifier:
        return None, None
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", identifier):
        return "email", identifier
    if re.match(r"^[0-9+\-]{6,20}$", identifier):
        return "phone", identifier
    return None, None


def _issue_customer_code(identifier: str):
    session["customer_login_identifier"] = identifier
    session["customer_login_code"] = DEFAULT_CUSTOMER_CODE
    return DEFAULT_CUSTOMER_CODE


def _build_public_vehicle_card(vehicle_row: dict, pricing_map: dict) -> dict:
    vehicle_id = vehicle_row["id"]
    photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
    cover_filename = _select_cover_filename(photo_rows)
    status = get_status(vehicle_id) or {}
    pricing = pricing_map.get(vehicle_id) if pricing_map else {}
    return {
        "id": vehicle_id,
        "vin": vehicle_row.get("vin"),
        "brand_cn": vehicle_row.get("brand_cn"),
        "brand_jp": vehicle_row.get("brand_jp"),
        "model_cn": vehicle_row.get("model_cn"),
        "model_jp": vehicle_row.get("model_jp"),
        "model_year_ad": vehicle_row.get("model_year_ad"),
        "mileage": status.get("mileage"),
        "cover_filename": cover_filename,
        "daily_price": pricing.get("daily_price") if pricing else None,
    }


@bp.get("/")
def portal_root():
    return render_template("portal/home.html", active_menu="portal")


@bp.get("/portal")
def portal_home():
    return render_template("portal/home.html", active_menu="portal")


@bp.get("/portal/management")
def portal_management():
    current_user = get_current_user()
    lang = request.args.get("lang")
    if current_user.is_authenticated:
        return redirect(url_for("ui.dashboard", lang=lang))
    session["next_url"] = url_for("ui.dashboard", lang=lang)
    return redirect(url_for("auth.login", lang=lang))


@bp.get("/portal/repair")
def portal_repair():
    return render_template("portal/repair.html", active_menu="portal")


@bp.get("/portal/trade")
def portal_trade():
    return render_template("portal/trade.html", active_menu="portal")


@bp.get("/portal/rentals")
def portal_rentals():
    vehicles, _ = list_vehicles(page=1, per_page=500)
    vehicle_ids = [row["id"] for row in vehicles]
    pricing_map = list_rental_pricing_for_vehicle_ids(vehicle_ids)
    cards = [_build_public_vehicle_card(row, pricing_map) for row in vehicles]
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
    customer = get_current_customer()
    next_url = request.args.get("next_url")
    if customer.is_authenticated:
        if next_url:
            return redirect(next_url)
        target = request.args.get("next") or "portal.portal_home"
        return redirect(url_for(target, lang=request.args.get("lang")))
    return render_template(
        "portal/customer_login.html",
        active_menu="portal",
        next_endpoint=request.args.get("next") or "portal.portal_home",
        next_url=next_url,
    )


@bp.get("/portal/customer-logout")
def portal_customer_logout():
    logout_customer()
    session.pop("customer_login_code", None)
    session.pop("customer_login_identifier", None)
    return redirect(url_for("portal.portal_home", lang=request.args.get("lang")))


@bp.post("/portal/customer-login")
def portal_customer_login_post():
    identifier = request.form.get("identifier", "").strip()
    code = request.form.get("code", "").strip()
    action = request.form.get("action") or "login"
    next_endpoint = request.form.get("next") or "portal.portal_home"
    next_url = request.form.get("next_url")

    identity_type, normalized = _detect_identity(identifier)
    if not identifier:
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            next_url=next_url,
            error="missing",
        )
    if not identity_type:
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            next_url=next_url,
            error="format",
        )
    if action == "send_code":
        customer = get_customer_by_identity(identity_type, normalized)
        if not customer or customer.get("status") != "active":
            return render_template(
                "portal/customer_login.html",
                active_menu="portal",
                next_endpoint=next_endpoint,
                next_url=next_url,
                identifier=identifier,
                error="invalid",
            )
        code_value = _issue_customer_code(normalized)
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            next_url=next_url,
            identifier=identifier,
            code_sent=True,
            code_value=code_value,
        )

    expected_code = session.get("customer_login_code")
    expected_identifier = session.get("customer_login_identifier")
    if not code or code != expected_code or normalized != expected_identifier:
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            next_url=next_url,
            identifier=identifier,
            error="code",
        )

    customer = get_customer_by_identity(identity_type, normalized)
    if not customer or customer.get("status") != "active":
        return render_template(
            "portal/customer_login.html",
            active_menu="portal",
            next_endpoint=next_endpoint,
            next_url=next_url,
            identifier=identifier,
            error="invalid",
        )
    login_customer(customer["id"])
    update_customer_last_login(customer["id"])
    session.pop("customer_login_code", None)
    session.pop("customer_login_identifier", None)
    if next_url:
        return redirect(next_url)
    return redirect(url_for(next_endpoint, lang=request.args.get("lang")))


@bp.get("/portal/rentals/<int:vehicle_id>")
def portal_rental_detail(vehicle_id: int):
    vehicle = get_vehicle_i18n(vehicle_id)
    if not vehicle:
        abort(404)
    status = get_status(vehicle_id) or {}
    pricing = get_rental_pricing(vehicle_id)
    photo_rows = list_vehicle_media(vehicle_id, PHOTO_FILE_TYPE)
    cover_filename = _select_cover_filename(photo_rows)
    photo_items = _media_items(photo_rows)
    rental_services = list_rental_services()
    stores = list_stores()
    delivery_tiers = list_delivery_fee_tiers()
    return render_template(
        "portal/rental_detail.html",
        active_menu="portal",
        vehicle=vehicle,
        status=status,
        pricing=pricing,
        cover_filename=cover_filename,
        vehicle_photos=photo_items,
        rental_services=rental_services,
        stores=stores,
        delivery_tiers=delivery_tiers,
        submitted=request.args.get("submitted") == "1",
        error=request.args.get("error"),
    )


@bp.post("/portal/rentals/<int:vehicle_id>/apply")
def portal_rental_request(vehicle_id: int):
    customer = get_current_customer()
    if not customer.is_authenticated:
        next_url = url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"))
        return redirect(url_for("portal.portal_customer_login", next_url=next_url, lang=request.args.get("lang")))
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    service_ids = [int(sid) for sid in request.form.getlist("service_ids") if sid.isdigit()]
    note = request.form.get("note")

    def _to_float(value: str | None):
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    if not start_date or not end_date:
        return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="dates"))

    vehicle = get_vehicle_i18n(vehicle_id) or {}
    pricing = get_rental_pricing(vehicle_id) or {}
    tiers = list_delivery_fee_tiers()

    pickup_method = request.form.get("pickup_method")
    dropoff_method = request.form.get("dropoff_method")
    pickup_store_id = request.form.get("pickup_store_id")
    dropoff_store_id = request.form.get("dropoff_store_id")
    pickup_address = request.form.get("pickup_address")
    dropoff_address = request.form.get("dropoff_address")
    pickup_lat = _to_float(request.form.get("pickup_lat"))
    pickup_lng = _to_float(request.form.get("pickup_lng"))
    dropoff_lat = _to_float(request.form.get("dropoff_lat"))
    dropoff_lng = _to_float(request.form.get("dropoff_lng"))

    if pickup_method not in {"store", "address"} or dropoff_method not in {"store", "address"}:
        return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="delivery"))

    def _store_by_id(value):
        if not value or not str(value).isdigit():
            return None
        return get_store(int(value))

    vehicle_store = _store_by_id(vehicle.get("garage_store_id")) or get_store(1)
    pickup_store = _store_by_id(pickup_store_id)
    dropoff_store = _store_by_id(dropoff_store_id)

    def _haversine(lat1, lng1, lat2, lng2):
        if None in (lat1, lng1, lat2, lng2):
            return None
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def _tier_fee(distance_km):
        if distance_km is None:
            return 0
        for tier in tiers:
            max_km = tier.get("max_km")
            if distance_km >= float(tier["min_km"]) and (max_km is None or distance_km <= float(max_km)):
                return int(tier["fee_amount"])
        return 0

    pickup_distance = None
    dropoff_distance = None
    pickup_fee = 0
    dropoff_fee = 0
    base_lat = vehicle_store.get("lat") if vehicle_store else None
    base_lng = vehicle_store.get("lng") if vehicle_store else None

    pickup_label = ""
    dropoff_label = ""

    if pickup_method == "address":
        if pickup_lat is None or pickup_lng is None:
            return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="delivery"))
        pickup_distance = _haversine(base_lat, base_lng, pickup_lat, pickup_lng)
        pickup_fee = _tier_fee(pickup_distance)
        pickup_label = pickup_address or "-"
    else:
        if not pickup_store_id and not vehicle_store:
            return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="delivery"))
        pickup_label = pickup_store.get("name") if pickup_store else vehicle_store.get("name") if vehicle_store else "-"

    if dropoff_method == "address":
        if dropoff_lat is None or dropoff_lng is None:
            return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="delivery"))
        dropoff_distance = _haversine(base_lat, base_lng, dropoff_lat, dropoff_lng)
        dropoff_fee = _tier_fee(dropoff_distance)
        dropoff_label = dropoff_address or "-"
    else:
        if not dropoff_store_id:
            return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="delivery"))
        dropoff_label = dropoff_store.get("name") if dropoff_store else "-"
        if dropoff_store and vehicle_store and dropoff_store.get("id") != vehicle_store.get("id"):
            store_distance = _haversine(base_lat, base_lng, dropoff_store.get("lat"), dropoff_store.get("lng"))
            dropoff_fee = int(_tier_fee(store_distance) * 0.5)

    def _days():
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return max((end - start).days + 1, 1)

    rental_days = _days()
    daily_price = pricing.get("daily_price") or 0
    insurance_per_day = pricing.get("insurance_per_day") or 0
    cleaning_fee = pricing.get("cleaning_fee") or 0
    deposit_amount = pricing.get("deposit_amount") or 0
    tax_rate = pricing.get("tax_rate") or 0

    service_items = []
    service_total = 0
    services = {row["id"]: row for row in list_rental_services()}
    for service_id in service_ids:
        row = services.get(service_id)
        if not row:
            continue
        price = row["price"]
        pricing_type = row["pricing_type"]
        item_total = price * rental_days if pricing_type == "per_day" else price
        service_items.append(
            {
                "service_id": service_id,
                "pricing_type": pricing_type,
                "unit_price": price,
                "total": item_total,
            }
        )
        service_total += item_total

    subtotal = (daily_price + insurance_per_day) * rental_days + cleaning_fee + pickup_fee + dropoff_fee + service_total
    total = subtotal

    price_snapshot = {
        "rental_days": rental_days,
        "daily_price": daily_price,
        "insurance_per_day": insurance_per_day,
        "cleaning_fee": cleaning_fee,
        "deposit_amount": deposit_amount,
        "pickup_fee": pickup_fee,
        "dropoff_fee": dropoff_fee,
        "pickup_distance_km": pickup_distance,
        "dropoff_distance_km": dropoff_distance,
        "service_items": service_items,
        "service_total": service_total,
        "tax_rate": tax_rate,
        "estimated_total": total,
        "pickup_label": pickup_label,
        "dropoff_label": dropoff_label,
        "note": note or "",
    }

    access_token = secrets.token_urlsafe(16)
    create_rental_booking(
        vehicle_id=vehicle_id,
        customer_id=customer.customer_id,
        start_date=start_date,
        end_date=end_date,
        pickup_method=pickup_method,
        pickup_store_id=int(pickup_store_id) if pickup_store_id and str(pickup_store_id).isdigit() else None,
        pickup_address=pickup_address,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        dropoff_method=dropoff_method,
        dropoff_store_id=int(dropoff_store_id) if dropoff_store_id and str(dropoff_store_id).isdigit() else None,
        dropoff_address=dropoff_address,
        dropoff_lat=dropoff_lat,
        dropoff_lng=dropoff_lng,
        price_snapshot=price_snapshot,
        access_token=access_token,
    )
    return redirect(url_for("portal.portal_rental_booking", access_token=access_token, lang=request.args.get("lang")))


@bp.get("/portal/rentals/booking/<access_token>")
def portal_rental_booking(access_token: str):
    booking = get_booking_by_token(access_token)
    if not booking:
        abort(404)
    snapshot = {}
    raw = booking.get("price_snapshot")
    if raw:
        try:
            snapshot = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            snapshot = {}
    services = {row["id"]: row for row in list_rental_services()}
    return render_template(
        "portal/rental_booking_magic.html",
        active_menu="portal",
        booking=booking,
        price_snapshot=snapshot,
        services=services,
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
