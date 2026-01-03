from typing import Optional

from ..db.mysql import fetch_all, fetch_one


def list_customers():
    return fetch_all(
        """
        SELECT id, customer_no, customer_type, display_name, full_name, status, last_login_at, created_at
        FROM customer
        ORDER BY id DESC
        """
    )


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
