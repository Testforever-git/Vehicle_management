# app/repositories/vehicle_repo.py
from app.db.mysql import fetch_all, fetch_one, execute

VEHICLE_COLUMNS = [
    "id",
    "vin",
    "plate_no",
    "brand_id",
    "model_id",
    "color_id",
    "model_year_ad",
    "model_year_era",
    "model_year_era_year",
    "type_designation_code",
    "classification_number",
    "engine_code",
    "engine_layout_code",
    "displacement_cc",
    "fuel_type_code",
    "drive_type_code",
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

_VEHICLE_COLUMN_CACHE = None
_VEHICLE_VIEW_CACHE = None
_VEHICLE_STATUS_CACHE = None


def _available_columns():
    global _VEHICLE_COLUMN_CACHE
    if _VEHICLE_COLUMN_CACHE is None:
        try:
            rows = fetch_all("SHOW COLUMNS FROM vehicle")
            _VEHICLE_COLUMN_CACHE = {row["Field"] for row in rows}
        except Exception:
            _VEHICLE_COLUMN_CACHE = set(VEHICLE_COLUMNS)
    return [c for c in VEHICLE_COLUMNS if c in _VEHICLE_COLUMN_CACHE]


def _select_columns():
    columns = [c for c in _available_columns() if c != "id"]
    if "id" not in columns:
        columns.append("id")
    return ", ".join(columns)


def _vehicle_view_name():
    global _VEHICLE_VIEW_CACHE
    if _VEHICLE_VIEW_CACHE is None:
        try:
            row = fetch_one(
                """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = DATABASE()
                  AND table_name = 'v_vehicle_i18n'
                """
            )
            _VEHICLE_VIEW_CACHE = "v_vehicle_i18n" if row else "vehicle"
        except Exception:
            _VEHICLE_VIEW_CACHE = "vehicle"
    return _VEHICLE_VIEW_CACHE


def _vehicle_status_available():
    global _VEHICLE_STATUS_CACHE
    if _VEHICLE_STATUS_CACHE is None:
        try:
            row = fetch_one(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'vehicle_status'
                """
            )
            _VEHICLE_STATUS_CACHE = bool(row)
        except Exception:
            _VEHICLE_STATUS_CACHE = False
    return _VEHICLE_STATUS_CACHE


def list_vehicles(filters=None, page=1, per_page=20):
    filters = filters or {}
    brand_keyword = (filters.get("brand") or "").strip()
    status = (filters.get("status") or "").strip()

    table_name = _vehicle_view_name()
    if _vehicle_status_available():
        base_sql = f"FROM {table_name} v LEFT JOIN vehicle_status vs ON vs.vehicle_id = v.id"
        status_select = "vs.status"
        fuel_select = "vs.fuel_level"
    else:
        base_sql = f"FROM {table_name} v"
        status_select = "NULL AS status"
        fuel_select = "NULL AS fuel_level"

    where_clauses = []
    params = []
    if brand_keyword and table_name == "v_vehicle_i18n":
        like_value = f"%{brand_keyword}%"
        where_clauses.append(
            "("
            "v.brand_cn LIKE %s OR v.brand_jp LIKE %s OR v.brand_code LIKE %s "
            "OR v.model_cn LIKE %s OR v.model_jp LIKE %s OR v.model_code LIKE %s"
            ")"
        )
        params.extend([like_value] * 6)
    if status and _vehicle_status_available():
        where_clauses.append("vs.status = %s")
        params.append(status)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_sql = f"SELECT COUNT(1) as total {base_sql} {where_sql}"
    total_row = fetch_one(count_sql, tuple(params))
    total = total_row["total"] if total_row else 0

    offset = max(page - 1, 0) * per_page
    if table_name == "v_vehicle_i18n":
        select_fields = f"""
          v.id, v.plate_no, v.vin, v.type_designation_code,
          v.garage_name, v.garage_address_jp, v.purchase_price,
          v.brand_cn, v.brand_jp, v.model_cn, v.model_jp, v.color_cn, v.color_jp,
          {status_select},
          {fuel_select}
        """
    else:
        select_fields = f"""
          v.id, v.plate_no, v.vin, v.type_designation_code,
          v.garage_name, v.garage_address_jp, v.purchase_price,
          {status_select},
          {fuel_select}
        """
    sql = f"""
    SELECT {select_fields}
    {base_sql}
    {where_sql}
    ORDER BY v.id DESC
    LIMIT %s OFFSET %s
    """
    rows = fetch_all(sql, tuple(params + [per_page, offset]))
    return rows, total


def get_vehicle_i18n(vehicle_id: int):
    table_name = _vehicle_view_name()
    sql = f"""
    SELECT *
    FROM {table_name}
    WHERE id = %s
    """
    r = fetch_one(sql, (vehicle_id,))
    if not r:
        return None
    return r

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


def upsert_status(vehicle_id: int, payload: dict):
    if not _vehicle_status_available():
        return 0
    fields = ["status", "mileage", "fuel_level", "location_desc", "update_time", "update_source"]
    columns = []
    values = []
    for field in fields:
        if field in payload:
            columns.append(field)
            values.append(payload[field])
    if not columns:
        return 0
    columns_sql = ", ".join(["vehicle_id"] + columns)
    placeholders = ", ".join(["%s"] * (len(columns) + 1))
    updates = ", ".join([f"{field} = VALUES({field})" for field in columns])
    sql = f"""
    INSERT INTO vehicle_status ({columns_sql})
    VALUES ({placeholders})
    ON DUPLICATE KEY UPDATE {updates}
    """
    return execute(sql, tuple([vehicle_id] + values))

def update_vehicle(vehicle_id: int, payload: dict):
    fields = [c for c in _available_columns() if c != "id"]
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
    fields = [c for c in _available_columns() if c != "id"]
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


def delete_vehicles(vehicle_ids: list[int]):
    if not vehicle_ids:
        return 0
    placeholders = ", ".join(["%s"] * len(vehicle_ids))
    sql = f"DELETE FROM vehicle WHERE id IN ({placeholders})"
    return execute(sql, tuple(vehicle_ids))
