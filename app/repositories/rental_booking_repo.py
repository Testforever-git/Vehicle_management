import json

from app.db.mysql import fetch_all, fetch_one, execute


def create_rental_booking(
    vehicle_id: int,
    customer_id: int,
    start_date: str,
    end_date: str,
    pickup_method: str,
    pickup_store_id: int | None,
    pickup_address: str | None,
    pickup_lat: float | None,
    pickup_lng: float | None,
    dropoff_method: str,
    dropoff_store_id: int | None,
    dropoff_address: str | None,
    dropoff_lat: float | None,
    dropoff_lng: float | None,
    price_snapshot: dict,
    access_token: str,
):
    execute(
        """
        INSERT INTO rental_booking (
          vehicle_id, customer_id, start_date, end_date,
          pickup_method, pickup_store_id, pickup_address, pickup_lat, pickup_lng,
          dropoff_method, dropoff_store_id, dropoff_address, dropoff_lat, dropoff_lng,
          price_snapshot, access_token, status
        ) VALUES (
          %s, %s, %s, %s,
          %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s,
          %s, %s, 'pending'
        )
        """,
        (
            vehicle_id,
            customer_id,
            start_date,
            end_date,
            pickup_method,
            pickup_store_id,
            pickup_address,
            pickup_lat,
            pickup_lng,
            dropoff_method,
            dropoff_store_id,
            dropoff_address,
            dropoff_lat,
            dropoff_lng,
            json.dumps(price_snapshot, ensure_ascii=False),
            access_token,
        ),
    )


def list_rental_bookings():
    return fetch_all(
        """
        SELECT
          rb.id,
          rb.vehicle_id,
          rb.customer_id,
          rb.start_date,
          rb.end_date,
          rb.pickup_method,
          rb.pickup_store_id,
          rb.pickup_address,
          rb.pickup_lat,
          rb.pickup_lng,
          rb.dropoff_method,
          rb.dropoff_store_id,
          rb.dropoff_address,
          rb.dropoff_lat,
          rb.dropoff_lng,
          rb.price_snapshot,
          rb.access_token,
          rb.status,
          rb.created_at,
          c.customer_no,
          c.display_name,
          c.full_name,
          v.vin,
          v.brand_cn,
          v.brand_jp,
          v.model_cn,
          v.model_jp,
          v.model_year_ad,
          v.store_name
        FROM rental_booking rb
        JOIN customer c ON c.id = rb.customer_id
        JOIN v_vehicle_i18n v ON v.id = rb.vehicle_id
        ORDER BY rb.created_at DESC
        """
    )


def get_booking_by_token(access_token: str):
    return fetch_one(
        """
        SELECT
          rb.*,
          v.vin,
          v.brand_cn,
          v.brand_jp,
          v.model_cn,
          v.model_jp,
          v.model_year_ad,
          v.store_name
        FROM rental_booking rb
        JOIN v_vehicle_i18n v ON v.id = rb.vehicle_id
        WHERE rb.access_token = %s
        """,
        (access_token,),
    )
