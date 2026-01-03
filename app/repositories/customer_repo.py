from typing import Optional

from ..db.mysql import fetch_all, fetch_one, execute


def list_customers(page: int = 1, per_page: int = 20):
    offset = max(page - 1, 0) * per_page
    return fetch_all(
        """
        SELECT
          c.id,
          c.customer_no,
          c.customer_type,
          c.display_name,
          c.full_name,
          c.status,
          c.last_login_at,
          c.created_at,
          email.identifier AS email,
          phone.identifier AS phone
        FROM customer c
        LEFT JOIN customer_auth_identity email
          ON email.customer_id = c.id
         AND email.identity_type = 'email'
         AND email.is_primary = 1
        LEFT JOIN customer_auth_identity phone
          ON phone.customer_id = c.id
         AND phone.identity_type = 'phone'
         AND phone.is_primary = 1
        ORDER BY c.id DESC
        LIMIT %s OFFSET %s
        """,
        (per_page, offset),
    )


def count_customers() -> int:
    row = fetch_one("SELECT COUNT(*) AS total FROM customer")
    return int(row["total"]) if row else 0


def get_customer_by_id(customer_id: int) -> Optional[dict]:
    return fetch_one(
        """
        SELECT id, customer_no, customer_type, display_name, full_name, status, last_login_at
        FROM customer
        WHERE id = %s
        """,
        (customer_id,),
    )


def get_customer_by_identity(identity_type: str, identifier: str) -> Optional[dict]:
    return fetch_one(
        """
        SELECT c.id, c.customer_no, c.display_name, c.full_name, c.status
        FROM customer c
        JOIN customer_auth_identity i ON i.customer_id = c.id
        WHERE i.identity_type = %s AND i.identifier = %s
        """,
        (identity_type, identifier),
    )


def update_customer_last_login(customer_id: int):
    execute(
        "UPDATE customer SET last_login_at = NOW() WHERE id = %s",
        (customer_id,),
    )


def soft_delete_customers(customer_ids: list[int]) -> int:
    if not customer_ids:
        return 0
    placeholders = ",".join(["%s"] * len(customer_ids))
    return execute(
        f"UPDATE customer SET status = 'deleted' WHERE id IN ({placeholders})",
        tuple(customer_ids),
    )
