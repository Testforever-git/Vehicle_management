import json

from app.db.mysql import fetch_all, fetch_one, execute


def create_rental_booking(
    vehicle_id: int,
    customer_id: int,
    start_date: str,
    end_date: str,
    pickup_mode: str,
    pickup_store_id: int | None,
    pickup_address_jp: str | None,
    pickup_postcode: str | None,
    pickup_lat: float | None,
    pickup_lng: float | None,
    dropoff_mode: str,
    dropoff_store_id: int | None,
    dropoff_address_jp: str | None,
    dropoff_postcode: str | None,
    dropoff_lat: float | None,
    dropoff_lng: float | None,
    price_snapshot: dict,
    note: str | None,
    booking_code: str,
    access_token: str,
    access_token_expires_at: str | None = None,
):
    execute(
        """
        INSERT INTO rental_booking (
          booking_code, customer_id, vehicle_id, start_date, end_date,
          pickup_mode, pickup_store_id, pickup_address_jp, pickup_postcode, pickup_lat, pickup_lng,
          dropoff_mode, dropoff_store_id, dropoff_address_jp, dropoff_postcode, dropoff_lat, dropoff_lng,
          price_snapshot, note, access_token, access_token_expires_at
        ) VALUES (
          %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s
        )
        """,
        (
            booking_code,
            customer_id,
            vehicle_id,
            start_date,
            end_date,
            pickup_mode,
            pickup_store_id,
            pickup_address_jp,
            pickup_postcode,
            pickup_lat,
            pickup_lng,
            dropoff_mode,
            dropoff_store_id,
            dropoff_address_jp,
            dropoff_postcode,
            dropoff_lat,
            dropoff_lng,
            json.dumps(price_snapshot, ensure_ascii=False),
            note,
            access_token,
            access_token_expires_at,
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
