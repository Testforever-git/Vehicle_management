from datetime import datetime

from app.repositories.customer_repo import get_customer_by_id
from app.repositories.vehicle_repo import get_vehicle_i18n

_VIRTUAL_REQUESTS: list[dict] = []
_NEXT_REQUEST_ID = 1


def create_rental_request(
    vehicle_id: int,
    customer_id: int,
    start_date: str,
    end_date: str,
    delivery_lat: float | None,
    delivery_lng: float | None,
    delivery_address: str | None,
    service_ids: list[int] | None,
    note: str | None,
):
    global _NEXT_REQUEST_ID
    vehicle = get_vehicle_i18n(vehicle_id) or {}
    customer = get_customer_by_id(customer_id) or {}
    request_data = {
        "id": _NEXT_REQUEST_ID,
        "vehicle_id": vehicle_id,
        "customer_id": customer_id,
        "start_date": start_date,
        "end_date": end_date,
        "delivery_lat": delivery_lat,
        "delivery_lng": delivery_lng,
        "delivery_address": delivery_address,
        "service_ids": service_ids or [],
        "note": note,
        "status": "new",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_no": customer.get("customer_no"),
        "display_name": customer.get("display_name"),
        "full_name": customer.get("full_name"),
        "vin": vehicle.get("vin"),
        "brand_cn": vehicle.get("brand_cn"),
        "brand_jp": vehicle.get("brand_jp"),
        "model_cn": vehicle.get("model_cn"),
        "model_jp": vehicle.get("model_jp"),
        "model_year_ad": vehicle.get("model_year_ad"),
    }
    _NEXT_REQUEST_ID += 1
    _VIRTUAL_REQUESTS.insert(0, request_data)


def list_rental_requests():
    return list(_VIRTUAL_REQUESTS)
