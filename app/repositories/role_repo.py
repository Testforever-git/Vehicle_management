from ..db.mysql import fetch_all, fetch_one


def list_roles():
    return fetch_all(
        """
        SELECT id, role_code, name_cn, name_jp, description
        FROM role
        ORDER BY id
        """
    )


def get_role_by_code(role_code: str):
    return fetch_one(
        """
        SELECT id, role_code, name_cn, name_jp, description
        FROM role
        WHERE role_code = %s
        """,
        (role_code,),
    )
