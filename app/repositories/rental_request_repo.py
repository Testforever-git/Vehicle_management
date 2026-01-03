import json

from app.db.mysql import fetch_all, execute


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
    payload = json.dumps(service_ids or [])
    execute(
        """
        INSERT INTO rental_request
          (vehicle_id, customer_id, start_date, end_date,
           delivery_lat, delivery_lng, delivery_address, service_ids, note, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'new')
        """,
        (
            vehicle_id,
            customer_id,
            start_date,
            end_date,
            delivery_lat,
            delivery_lng,
            delivery_address,
            payload,
            note,
        ),
    )


def list_rental_requests():
    return fetch_all(
        """
        SELECT
          rr.id,
          rr.vehicle_id,
          rr.customer_id,
          rr.start_date,
          rr.end_date,
          rr.delivery_lat,
          rr.delivery_lng,
          rr.delivery_address,
          rr.service_ids,
          rr.note,
          rr.status,
          rr.created_at,
          c.customer_no,
          c.display_name,
          c.full_name,
          v.vin,
          v.brand_cn,
          v.brand_jp,
          v.model_cn,
          v.model_jp,
          v.model_year_ad
        FROM rental_request rr
        JOIN customer c ON c.id = rr.customer_id
        JOIN v_vehicle_i18n v ON v.id = rr.vehicle_id
        ORDER BY rr.created_at DESC
        """
    )
