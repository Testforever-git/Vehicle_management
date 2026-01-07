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
from ...repositories.rental_request_repo import create_rental_request
from ...repositories.rental_booking_repo import create_rental_booking
from ...repositories.rental_pricing_repo import get_rental_pricing
from ...repositories.rental_service_repo import get_rental_service_by_ids
from ...repositories.vehicle_repo import get_vehicle_i18n
from ...repositories.store_repo import get_store_by_id
from ...repositories.rental_delivery_fee_repo import get_delivery_fee_by_distance
import secrets
import json
from datetime import datetime, timedelta
from ...security.customers import get_current_customer, login_customer, logout_customer
from ...security.users import get_current_user

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
    
    # 获取门店列表
    from ...repositories.store_repo import list_stores
    stores = list_stores()
    
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
        submitted=request.args.get("submitted") == "1",
        error=request.args.get("error"),
    )


@bp.get("/portal/rental-booking/<token>")
def portal_rental_booking_magic(token: str):
    """订单确认及支付页面（魔页）"""
    from ...repositories.rental_booking_repo import get_booking_by_token
    from ...repositories.rental_service_repo import list_rental_services
    
    booking = get_booking_by_token(token)
    if not booking:
        abort(404)
    
    # 解析价格快照
    price_snapshot = json.loads(booking["price_snapshot"]) if isinstance(booking["price_snapshot"], str) else booking["price_snapshot"]
    
    # 获取服务信息
    service_rows = list_rental_services()
    services = {row["id"]: row for row in service_rows}
    
    return render_template(
        "portal/rental_booking_magic.html",
        active_menu="portal",
        booking=booking,
        price_snapshot=price_snapshot,
        services=services,
    )


@bp.post("/portal/rentals/<int:vehicle_id>/apply")
def portal_rental_request(vehicle_id: int):
    customer = get_current_customer()
    if not customer.is_authenticated:
        next_url = url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"))
        return redirect(url_for("portal.portal_customer_login", next_url=next_url, lang=request.args.get("lang")))
    
    # 获取表单数据
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    pickup_mode = request.form.get("pickup_mode", "store")  # 'store' or 'delivery'
    pickup_store_id = request.form.get("pickup_store_id")
    pickup_address_jp = request.form.get("pickup_address_jp")
    pickup_postcode = request.form.get("pickup_postcode")
    pickup_lat = request.form.get("pickup_lat")
    pickup_lng = request.form.get("pickup_lng")
    dropoff_mode = request.form.get("dropoff_mode", "store")  # 'store' or 'return_to_any' (return to any store)
    dropoff_store_id = request.form.get("dropoff_store_id")
    dropoff_address_jp = request.form.get("dropoff_address_jp")
    dropoff_postcode = request.form.get("dropoff_postcode")
    dropoff_lat = request.form.get("dropoff_lat")
    dropoff_lng = request.form.get("dropoff_lng")
    service_ids = [int(sid) for sid in request.form.getlist("service_ids") if sid.isdigit()]
    note = request.form.get("note")

    def _to_float(value: str | None):
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _to_int(value: str | None):
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    if not start_date or not end_date:
        return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="dates"))
    
    # 计算租车天数
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    rental_days = (end_dt - start_dt).days + 1
    
    # 获取车辆信息
    vehicle = get_vehicle_i18n(vehicle_id)
    if not vehicle:
        return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="vehicle_not_found"))
    
    # 获取定价信息
    pricing = get_rental_pricing(vehicle_id)
    if not pricing:
        return redirect(url_for("portal.portal_rental_detail", vehicle_id=vehicle_id, lang=request.args.get("lang"), error="pricing_not_found"))
    
    # 计算基础费用
    base_rent = pricing["daily_price"] * rental_days
    insurance_total = pricing["insurance_per_day"] * rental_days
    cleaning_fee = pricing.get("cleaning_fee", 0)
    
    # 计算交车费用
    pickup_fee = 0
    pickup_label = ""
    if pickup_mode == "delivery":
        # 计算从车辆所在门店到交车地址的距离
        vehicle_store_id = vehicle.get("garage_store_id") or 1  # 如果车辆不属于任何门店，则使用ID为1的门店
        vehicle_store = get_store_by_id(vehicle_store_id)
        if vehicle_store:
            # 计算距离（这里简化为使用经纬度计算距离）
            import math
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371  # 地球半径（公里）
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat/2)**2 + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                return R * c
            
            distance = haversine_distance(
                vehicle_store["lat"], 
                vehicle_store["lng"], 
                _to_float(pickup_lat), 
                _to_float(pickup_lng)
            )
            # 获取距离对应的费用
            fee_tier = get_delivery_fee_by_distance(distance)
            if fee_tier and fee_tier["action"] == "fixed_fee":
                pickup_fee = fee_tier["fee"] or 0
            pickup_label = f"配送到地址: {pickup_address_jp or f'{pickup_lat}, {pickup_lng}'}"
        else:
            pickup_label = f"配送到地址: {pickup_address_jp or f'{pickup_lat}, {pickup_lng}'}"
    else:
        # 从门店取车
        if pickup_store_id:
            pickup_store = get_store_by_id(_to_int(pickup_store_id))
            if pickup_store:
                pickup_label = f"门店取车: {pickup_store['name']}"
            else:
                pickup_label = "门店取车"
        else:
            pickup_label = "门店取车"
    
    # 计算还车费用
    dropoff_fee = 0
    dropoff_label = ""
    if dropoff_mode == "delivery":
        # 计算从还车地址到车辆所在门店的距离
        vehicle_store_id = vehicle.get("garage_store_id") or 1  # 如果车辆不属于任何门店，则使用ID为1的门店
        vehicle_store = get_store_by_id(vehicle_store_id)
        if vehicle_store:
            # 计算距离（这里简化为使用经纬度计算距离）
            import math
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371  # 地球半径（公里）
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat/2)**2 + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                return R * c
            
            distance = haversine_distance(
                _to_float(dropoff_lat), 
                _to_float(dropoff_lng),
                vehicle_store["lat"], 
                vehicle_store["lng"]
            )
            # 获取距离对应的费用
            fee_tier = get_delivery_fee_by_distance(distance)
            if fee_tier and fee_tier["action"] == "fixed_fee":
                dropoff_fee = fee_tier["fee"] or 0
            dropoff_label = f"还车到地址: {dropoff_address_jp or f'{dropoff_lat}, {dropoff_lng}'}"
        else:
            dropoff_label = f"还车到地址: {dropoff_address_jp or f'{dropoff_lat}, {dropoff_lng}'}"
    elif dropoff_mode == "return_to_any" and dropoff_store_id:
        # 如果选择还到其他门店，计算两个门店之间的距离并费用减半
        vehicle_store_id = vehicle.get("garage_store_id") or 1  # 如果车辆不属于任何门店，则使用ID为1的门店
        vehicle_store = get_store_by_id(vehicle_store_id)
        dropoff_store = get_store_by_id(_to_int(dropoff_store_id))
        
        if vehicle_store and dropoff_store:
            import math
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371  # 地球半径（公里）
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat/2)**2 + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                return R * c
            
            distance = haversine_distance(
                vehicle_store["lat"], 
                vehicle_store["lng"],
                dropoff_store["lat"], 
                dropoff_store["lng"]
            )
            # 获取距离对应的费用并减半
            fee_tier = get_delivery_fee_by_distance(distance)
            if fee_tier and fee_tier["action"] == "fixed_fee":
                dropoff_fee = (fee_tier["fee"] or 0) // 2  # 费用减半
            dropoff_label = f"还车到门店: {dropoff_store['name']}"
        else:
            dropoff_label = f"还车到门店: {dropoff_store['name'] if dropoff_store else '未知门店'}"
    else:
        # 默认还到取车门店
        if pickup_store_id:
            pickup_store = get_store_by_id(_to_int(pickup_store_id))
            dropoff_label = f"还车到门店: {pickup_store['name'] if pickup_store else '取车门店'}"
        else:
            dropoff_label = "还车到取车门店"
    
    # 计算服务费用
    service_total = 0
    service_items = []
    if service_ids:
        services = get_rental_service_by_ids(service_ids)
        for service in services:
            if service["pricing_type"] == "per_day":
                item_total = service["price"] * rental_days
            elif service["pricing_type"] == "per_booking":
                item_total = service["price"]
            else:
                item_total = service["price"]  # 默认按预订收费
            
            service_total += item_total
            service_items.append({
                "service_id": service["id"],
                "name": service["name_jp"],  # 使用日文名称作为示例
                "total": item_total
            })
    
    # 总费用
    estimated_total = base_rent + insurance_total + cleaning_fee + pickup_fee + dropoff_fee + service_total
    
    # 创建价格快照
    price_snapshot = {
        "pricing_version": "v1",
        "rental_days": rental_days,
        "daily_price": pricing["daily_price"],
        "base_rent": base_rent,
        "insurance_per_day": pricing["insurance_per_day"],
        "insurance_total": insurance_total,
        "cleaning_fee": cleaning_fee,
        "pickup_fee": pickup_fee,
        "dropoff_fee": dropoff_fee,
        "service_total": service_total,
        "service_items": service_items,
        "estimated_total": estimated_total,
        "deposit_amount": pricing.get("deposit_amount", 0),
        "pickup_label": pickup_label,
        "dropoff_label": dropoff_label,
        "note": note
    }
    
    # 生成访问令牌
    access_token = secrets.token_urlsafe(32)
    access_token_expires_at = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    
    # 生成订单号
    booking_code = f"RB{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(4).upper()}"
    
    # 创建订单
    create_rental_booking(
        vehicle_id=vehicle_id,
        customer_id=customer.customer_id,
        start_date=start_date,
        end_date=end_date,
        pickup_mode=pickup_mode,
        pickup_store_id=_to_int(pickup_store_id),
        pickup_address_jp=pickup_address_jp,
        pickup_postcode=pickup_postcode,
        pickup_lat=_to_float(pickup_lat),
        pickup_lng=_to_float(pickup_lng),
        dropoff_mode=dropoff_mode,
        dropoff_store_id=_to_int(dropoff_store_id),
        dropoff_address_jp=dropoff_address_jp,
        dropoff_postcode=dropoff_postcode,
        dropoff_lat=_to_float(dropoff_lat),
        dropoff_lng=_to_float(dropoff_lng),
        price_snapshot=price_snapshot,
        note=note,
        booking_code=booking_code,
        access_token=access_token,
        access_token_expires_at=access_token_expires_at,
    )
    
    # 跳转到订单确认页面（使用访问令牌）
    return redirect(url_for("portal.portal_rental_booking_magic", token=access_token, lang=request.args.get("lang")))


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
