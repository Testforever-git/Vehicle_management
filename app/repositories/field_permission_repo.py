from ..db.mysql import fetch_all, execute


def list_field_permissions():
    return fetch_all(
        """
        SELECT id, table_name, field_name, access_level, min_role_code,
               is_visible, is_editable, description
        FROM vehicle_field_permission
        ORDER BY table_name, field_name
        """
    )


def update_field_permission(
    permission_id: int,
    access_level: str,
    min_role_code: str,
    is_visible: bool,
    is_editable: bool,
    description: str,
):
    execute(
        """
        UPDATE vehicle_field_permission
        SET access_level = %s,
            min_role_code = %s,
            is_visible = %s,
            is_editable = %s,
            description = %s
        WHERE id = %s
        """,
        (access_level, min_role_code, int(is_visible), int(is_editable), description, permission_id),
    )
