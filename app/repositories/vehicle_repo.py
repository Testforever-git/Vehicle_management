# app/repositories/vehicle_repo.py
from app.db.mysql import fetch_all, fetch_one, execute

def _default_dirs(vehicle_id: int):
    car_no = f"{vehicle_id:06d}"
    return (
        f"db/image/{car_no}/legal_doc",
        f"db/image/{car_no}/vehicle_photo",
    )

def list_vehicles():
    sql = """
    SELECT
      id, brand_jp, model_jp, plate_no, vin, type_designation_code,
      garage_name, garage_address_jp, purchase_price,
      legal_doc_dir, vehicle_photo_dir
    FROM vehicle
    ORDER BY id DESC
    LIMIT 200
    """
    rows = fetch_all(sql)
    for r in rows:
        ld, vp = _default_dirs(r["id"])
        if not r.get("legal_doc_dir"):
            r["legal_doc_dir"] = ld
        if not r.get("vehicle_photo_dir"):
            r["vehicle_photo_dir"] = vp
    return rows

def get_vehicle(vehicle_id: int):
    sql = """
    SELECT
      id, brand_jp, model_jp, plate_no, vin, type_designation_code,
      garage_name, garage_address_jp, purchase_price,
      legal_doc_dir, vehicle_photo_dir
    FROM vehicle
    WHERE id = %s
    """
    r = fetch_one(sql, (vehicle_id,))
    if not r:
        return None
    ld, vp = _default_dirs(r["id"])
    if not r.get("legal_doc_dir"):
        r["legal_doc_dir"] = ld
    if not r.get("vehicle_photo_dir"):
        r["vehicle_photo_dir"] = vp
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
    # 只允许更新这些字段（最小闭环）
    fields = ["brand_jp","model_jp","type_designation_code","garage_name","garage_address_jp","purchase_price"]
    sets = []
    params = []
    for f in fields:
        if f in payload:
            sets.append(f"{f} = %s")
            params.append(payload[f])
    if not sets:
        return 0
    params.append(vehicle_id)
    sql = f"UPDATE vehicle SET {', '.join(sets)} WHERE id = %s"
    return execute(sql, tuple(params))

def ensure_dirs_saved(vehicle_id: int):
    """
    可选：把默认目录写回 DB，确保后续业务都能直接用列值。
    """
    v = get_vehicle(vehicle_id)
    if not v:
        return 0
    sql = """
    UPDATE vehicle
    SET legal_doc_dir = %s, vehicle_photo_dir = %s
    WHERE id = %s
    """
    return execute(sql, (v["legal_doc_dir"], v["vehicle_photo_dir"], vehicle_id))
