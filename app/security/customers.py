from dataclasses import dataclass
from typing import Optional

from flask import session

from ..repositories.customer_repo import get_customer_by_id


@dataclass
class CurrentCustomer:
    is_authenticated: bool
    display_name: str
    customer_id: Optional[int] = None
    customer_no: str = ""


def get_current_customer() -> CurrentCustomer:
    try:
        customer_id = session.get("customer_id")
        if customer_id:
            row = get_customer_by_id(int(customer_id))
            if row and row.get("status") == "active":
                return CurrentCustomer(
                    True,
                    display_name=row.get("display_name") or row.get("full_name") or row.get("customer_no"),
                    customer_id=row.get("id"),
                    customer_no=row.get("customer_no") or "",
                )
        return CurrentCustomer(False, display_name="guest")
    except Exception:
        return CurrentCustomer(False, display_name="guest")


def login_customer(customer_id: int):
    session["customer_id"] = customer_id


def logout_customer():
    session.pop("customer_id", None)
