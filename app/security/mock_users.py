from dataclasses import dataclass
from flask import session


@dataclass
class CurrentUser:
    is_authenticated: bool
    username: str
    role_code: str
    full_name: str = ""


def get_current_user() -> CurrentUser:
    try:
        username = session.get("username")
        role_code = session.get("role_code")
        if username and role_code:
            return CurrentUser(True, username=username, role_code=role_code, full_name=username)
        return CurrentUser(False, username="guest", role_code="public", full_name="")
    except:
        # 如果 session 相关操作失败，返回默认用户
        return CurrentUser(False, username="guest", role_code="public", full_name="")


def login_as(username: str, role_code: str):
    session["username"] = username
    session["role_code"] = role_code


def logout():
    session.pop("username", None)
    session.pop("role_code", None)
