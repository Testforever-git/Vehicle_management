from app.db.mysql import fetch_all


def list_delivery_fee_tiers():
    return fetch_all(
        """
        SELECT id, min_km, max_km, fee_amount, currency
        FROM rental_delivery_fee_tier
        WHERE is_active = 1
        ORDER BY min_km ASC
        """
    )
