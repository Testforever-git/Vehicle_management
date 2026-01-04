from app.db.mysql import fetch_all, execute


def list_rental_services(include_inactive: bool = False):
    sql = """
        SELECT id, code, name_jp, name_cn, pricing_type, price, currency, is_active
        FROM rental_service_catalog
    """
    params: tuple = ()
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY id DESC"
    return fetch_all(sql, params)


def create_rental_service(
    code: str,
    name_jp: str,
    name_cn: str,
    pricing_type: str,
    price: int,
    currency: str,
    is_active: bool,
):
    execute(
        """
        INSERT INTO rental_service_catalog
          (code, name_jp, name_cn, pricing_type, price, currency, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (code, name_jp, name_cn, pricing_type, price, currency, int(is_active)),
    )


def update_rental_service(
    service_id: int,
    code: str,
    name_jp: str,
    name_cn: str,
    pricing_type: str,
    price: int,
    currency: str,
    is_active: bool,
):
    execute(
        """
        UPDATE rental_service_catalog
        SET code = %s,
            name_jp = %s,
            name_cn = %s,
            pricing_type = %s,
            price = %s,
            currency = %s,
            is_active = %s
        WHERE id = %s
        """,
        (code, name_jp, name_cn, pricing_type, price, currency, int(is_active), service_id),
    )
