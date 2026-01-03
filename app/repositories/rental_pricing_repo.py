from app.db.mysql import fetch_all, fetch_one, execute


def list_rental_pricing():
    return fetch_all(
        """
        SELECT
          v.id AS vehicle_id,
          v.vin,
          v.brand_cn,
          v.brand_jp,
          v.model_cn,
          v.model_jp,
          v.model_year_ad,
          p.currency,
          p.daily_price,
          p.deposit_amount,
          p.insurance_per_day,
          p.free_km_per_day,
          p.extra_km_price,
          p.cleaning_fee,
          p.late_fee_per_day,
          p.tax_rate,
          p.updated_at
        FROM v_vehicle_i18n v
        LEFT JOIN rental_vehicle_pricing p ON p.vehicle_id = v.id
        ORDER BY v.id DESC
        """
    )


def get_rental_pricing(vehicle_id: int):
    return fetch_one(
        """
        SELECT *
        FROM rental_vehicle_pricing
        WHERE vehicle_id = %s
        """,
        (vehicle_id,),
    )


def upsert_rental_pricing(
    vehicle_id: int,
    currency: str,
    daily_price: int,
    deposit_amount: int,
    insurance_per_day: int,
    free_km_per_day: int | None,
    extra_km_price: int | None,
    cleaning_fee: int,
    late_fee_per_day: int,
    tax_rate: float,
    updated_by: int | None,
):
    execute(
        """
        INSERT INTO rental_vehicle_pricing
          (vehicle_id, currency, daily_price, deposit_amount, insurance_per_day,
           free_km_per_day, extra_km_price, cleaning_fee, late_fee_per_day, tax_rate, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          currency = VALUES(currency),
          daily_price = VALUES(daily_price),
          deposit_amount = VALUES(deposit_amount),
          insurance_per_day = VALUES(insurance_per_day),
          free_km_per_day = VALUES(free_km_per_day),
          extra_km_price = VALUES(extra_km_price),
          cleaning_fee = VALUES(cleaning_fee),
          late_fee_per_day = VALUES(late_fee_per_day),
          tax_rate = VALUES(tax_rate),
          updated_by = VALUES(updated_by),
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            vehicle_id,
            currency,
            daily_price,
            deposit_amount,
            insurance_per_day,
            free_km_per_day,
            extra_km_price,
            cleaning_fee,
            late_fee_per_day,
            tax_rate,
            updated_by,
        ),
    )
