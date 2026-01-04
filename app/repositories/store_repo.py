from app.db.mysql import fetch_all, execute


def list_stores():
    return fetch_all(
        """
        SELECT id, name
        FROM store
        WHERE is_active = 1
        ORDER BY id DESC
        """
    )


def create_store(
    name: str,
    address_jp: str,
    postcode: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    phone: str | None = None,
    is_active: bool = True,
):
    execute(
        """
        INSERT INTO store (name, address_jp, postcode, lat, lng, phone, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (name, address_jp, postcode, lat, lng, phone, int(is_active)),
    )
