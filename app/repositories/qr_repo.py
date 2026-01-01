# app/repositories/qr_repo.py
import uuid

from app.db.mysql import fetch_one, execute

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


def get_vehicle_id_by_qr_slug(qr_slug: str):
    sql = """
    SELECT vehicle_id
    FROM vehicle_qr
    WHERE qr_slug = %s AND is_active = 1
    """
    row = fetch_one(sql, (qr_slug,))
    return row["vehicle_id"] if row else None


def get_vehicle_qr_by_vehicle_id(vehicle_id: int):
    sql = """
    SELECT qr_slug
    FROM vehicle_qr
    WHERE vehicle_id = %s AND is_active = 1
    """
    return fetch_one(sql, (vehicle_id,))


def ensure_vehicle_qr(vehicle_id: int):
    existing = get_vehicle_qr_by_vehicle_id(vehicle_id)
    if existing and existing.get("qr_slug"):
        return existing["qr_slug"]
    qr_slug = uuid.uuid4().hex[:12]
    execute(
        """
        INSERT INTO vehicle_qr (vehicle_id, qr_slug, is_active)
        VALUES (%s, %s, 1)
        """,
        (vehicle_id, qr_slug),
    )
    return qr_slug
