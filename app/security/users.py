from dataclasses import dataclass
from typing import Optional
from flask import session

from ..repositories.user_repo import get_user_by_id


@dataclass
class CurrentUser:
    is_authenticated: bool
    username: str
    role_code: str
    full_name: str = ""
    user_id: Optional[int] = None


def get_current_user() -> CurrentUser:
    try:
        user_id = session.get("user_id")
        if user_id:
            row = get_user_by_id(int(user_id))
            if row and row.get("is_active"):
                return CurrentUser(
                    True,
                    username=row["username"],
                    role_code=row["role_code"],
                    full_name=row.get("full_name") or row["username"],
                    user_id=row["id"],
                )
        return CurrentUser(False, username="guest", role_code="public", full_name="")
    except Exception:
        return CurrentUser(False, username="guest", role_code="public", full_name="")


def login_user(user_id: int):
    session["user_id"] = user_id


def logout():
    session.pop("user_id", None)
