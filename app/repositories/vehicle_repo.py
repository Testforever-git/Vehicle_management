# app/repositories/vehicle_repo.py
import json

from app.db.mysql import fetch_all, fetch_one, execute

VEHICLE_COLUMNS = [
    "id",
    "vin",
    "plate_no",
    "brand_cn",
    "brand_jp",
    "model_cn",
    "model_jp",
    "color_cn",
    "color_jp",
    "model_year",
    "type_designation_code",
    "classification_number",
    "engine_code",
    "engine_layout",
    "displacement_cc",
    "fuel_type",
    "drive_type",
    "transmission",
    "ownership_type",
    "owner_id",
    "driver_id",
    "garage_name",
    "garage_address_jp",
    "garage_address_cn",
    "garage_postcode",
    "garage_lat",
    "garage_lng",
    "purchase_date",
    "purchase_price",
    "ext_json",
    "note",
    "updated_by",
]


def _select_columns():
    return ", ".join([c for c in VEHICLE_COLUMNS if c != "id"]) + ", id"


def list_vehicles():
    sql = """
    SELECT
      id, brand_jp, model_jp, plate_no, vin, type_designation_code,
      garage_name, garage_address_jp, purchase_price
    FROM vehicle
    ORDER BY id DESC
    LIMIT 200
    """
    rows = fetch_all(sql)
    return rows

def get_vehicle(vehicle_id: int):
    sql = f"""
    SELECT {_select_columns()}
    FROM vehicle
    WHERE id = %s
    """
    r = fetch_one(sql, (vehicle_id,))
    if not r:
        return None
    return r


def get_vehicle_by_vin(vin: str):
    sql = f"""
    SELECT {_select_columns()}
    FROM vehicle
    WHERE vin = %s
    """
    r = fetch_one(sql, (vin,))
    if not r:
        return None
    return r

def get_status(vehicle_id: int):
    # 你若还没建 vehicle_status 表，可以先建空表或注释这段
    sql = """
    SELECT status, mileage, fuel_level, location_desc, update_time
    FROM vehicle_status
    WHERE vehicle_id = %s
    """
    return fetch_one(sql, (vehicle_id,))

def update_vehicle(vehicle_id: int, payload: dict):
    fields = [c for c in VEHICLE_COLUMNS if c != "id"]
    sets = []
    params = []
    for f in fields:
        if f in payload:
            sets.append(f"{f} = %s")
            params.append(payload[f])
    if not sets:
        return 0
    sets.append("updated_at = NOW()")
    params.append(vehicle_id)
    sql = f"UPDATE vehicle SET {', '.join(sets)} WHERE id = %s"
    return execute(sql, tuple(params))


def create_vehicle(payload: dict):
    fields = [c for c in VEHICLE_COLUMNS if c != "id"]
    values = []
    params = []
    for f in fields:
        if f in payload:
            values.append(f)
            params.append(payload[f])
    if not values:
        return 0
    placeholders = ", ".join(["%s"] * len(values))
    sql = f"INSERT INTO vehicle ({', '.join(values)}) VALUES ({placeholders})"
    return execute(sql, tuple(params))
