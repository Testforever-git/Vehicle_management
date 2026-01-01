from ..db.mysql import fetch_all, execute


def list_field_permissions(role_id: int):
    return fetch_all(
        """
        SELECT id, table_name, field_name, access_level, description
        FROM vehicle_field_permission
        WHERE role_id = %s
        ORDER BY table_name, field_name
        """,
        (role_id,),
    )


def list_field_permissions_admin():
    return fetch_all(
        """
        SELECT vfp.id, vfp.role_id, r.role_code, r.name_cn, r.name_jp,
               vfp.table_name, vfp.field_name, vfp.access_level, vfp.description
        FROM vehicle_field_permission vfp
        JOIN role r ON vfp.role_id = r.id
        ORDER BY r.role_code, vfp.table_name, vfp.field_name
        """
        SELECT table_name, field_name
        FROM field_catalog
        ORDER BY table_name, field_name
        """
    )


def refresh_field_catalog():
    execute(
        """
        REPLACE INTO field_catalog (table_name, field_name, data_type, is_nullable)
        SELECT table_name, column_name, data_type, (is_nullable = 'YES')
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name LIKE 'vehicle%'
        """
    )


def upsert_field_permission(
    role_id: int,
    table_name: str,
    field_name: str,
    access_level: int,
    description: str,
):
    execute(
        """
        INSERT INTO vehicle_field_permission
        (role_id, table_name, field_name, access_level, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_level = VALUES(access_level),
            description = VALUES(description),
            updated_at = CURRENT_TIMESTAMP
        """,
        (role_id, table_name, field_name, access_level, description),
    )


def list_field_catalog():
    return fetch_all(
        """
        SELECT table_name, field_name
        FROM field_catalog
        ORDER BY table_name, field_name
        """
    )


def refresh_field_catalog():
    execute(
        """
        REPLACE INTO field_catalog (table_name, field_name, data_type, is_nullable)
        SELECT table_name, column_name, data_type, (is_nullable = 'YES')
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name LIKE 'vehicle%'
        """
    )


def upsert_field_permission(
    role_id: int,
    table_name: str,
    field_name: str,
    access_level: int,
    description: str,
):
    execute(
        """
        INSERT INTO vehicle_field_permission
        (role_id, table_name, field_name, access_level, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_level = VALUES(access_level),
            description = VALUES(description),
            updated_at = CURRENT_TIMESTAMP
        """,
        (role_id, table_name, field_name, access_level, description),
    )


def update_field_permission(
    permission_id: int,
    role_id: int,
    table_name: str,
    field_name: str,
    access_level: int,
    description: str,
):
    execute(
        """
        UPDATE vehicle_field_permission
        SET role_id = %s,
            table_name = %s,
            field_name = %s,
            access_level = %s,
            description = %s
        WHERE id = %s
        """,
        (role_id, table_name, field_name, access_level, description, permission_id),
    )


def delete_field_permission(role_id: int, table_name: str, field_name: str):
    execute(
        """
        DELETE FROM vehicle_field_permission
        WHERE role_id = %s AND table_name = %s AND field_name = %s
        """,
        (role_id, table_name, field_name),
    )
