from ..db.mysql import fetch_all


def list_role_permissions(role_code: str):
    return fetch_all(
        """
        SELECT rp.module_name, rp.permission_type, rp.allow_flag
        FROM role_permission rp
        JOIN role r ON rp.role_id = r.id
        WHERE r.role_code = %s
        """,
        (role_code,),
    )
