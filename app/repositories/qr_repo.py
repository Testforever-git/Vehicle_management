# app/repositories/qr_repo.py
from app.db.mysql import fetch_one

def get_vehicle_by_qr_slug(qr_slug: str):
    """
    Requires table: vehicle_qr (qr_slug UNIQUE, vehicle_id FK).
    If you haven't created vehicle_qr yet, see the fallback option below.
    """
    sql = """
    SELECT v.*
    FROM vehicle_qr q
    JOIN v_vehicle_i18n v ON v.id = q.vehicle_id
    WHERE q.qr_slug = %s AND q.is_active = 1
    """
    try:
        return fetch_one(sql, (qr_slug,))
    except Exception:
        fallback_sql = """
        SELECT v.*
        FROM vehicle_qr q
        JOIN vehicle v ON v.id = q.vehicle_id
        WHERE q.qr_slug = %s AND q.is_active = 1
        """
        return fetch_one(fallback_sql, (qr_slug,))
