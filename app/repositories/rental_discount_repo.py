from app.db.mysql import fetch_all, execute


def list_rental_discount_rules():
    return fetch_all(
        """
        SELECT
          r.id,
          r.vehicle_id,
          r.min_days,
          r.max_days,
          r.discount_type,
          r.discount_value,
          r.priority,
          r.is_active,
          r.valid_from,
          r.valid_to,
          v.brand_cn,
          v.brand_jp,
          v.model_cn,
          v.model_jp,
          v.model_year_ad
        FROM rental_longterm_discount_rule r
        JOIN v_vehicle_i18n v ON v.id = r.vehicle_id
        ORDER BY r.vehicle_id, r.priority, r.min_days
        """
    )


def create_rental_discount_rule(
    vehicle_id: int,
    min_days: int,
    max_days: int | None,
    discount_type: str,
    discount_value: int,
    priority: int,
    is_active: bool,
    valid_from: str | None,
    valid_to: str | None,
):
    execute(
        """
        INSERT INTO rental_longterm_discount_rule
          (vehicle_id, min_days, max_days, discount_type, discount_value,
           priority, is_active, valid_from, valid_to)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            vehicle_id,
            min_days,
            max_days,
            discount_type,
            discount_value,
            priority,
            int(is_active),
            valid_from,
            valid_to,
        ),
    )


def update_rental_discount_rule(
    rule_id: int,
    vehicle_id: int,
    min_days: int,
    max_days: int | None,
    discount_type: str,
    discount_value: int,
    priority: int,
    is_active: bool,
    valid_from: str | None,
    valid_to: str | None,
):
    execute(
        """
        UPDATE rental_longterm_discount_rule
        SET vehicle_id = %s,
            min_days = %s,
            max_days = %s,
            discount_type = %s,
            discount_value = %s,
            priority = %s,
            is_active = %s,
            valid_from = %s,
            valid_to = %s
        WHERE id = %s
        """,
        (
            vehicle_id,
            min_days,
            max_days,
            discount_type,
            discount_value,
            priority,
            int(is_active),
            valid_from,
            valid_to,
            rule_id,
        ),
    )
