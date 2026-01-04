from app.db.mysql import fetch_all


def list_delivery_fee_tiers():
    return fetch_all(
        """
        SELECT id, min_km, max_km, action, fee, note, is_active, priority
        FROM rental_delivery_fee_tier
        WHERE is_active = 1
        ORDER BY priority ASC, min_km ASC
        """
    )
