from ..db.mysql import fetch_all, fetch_one, execute

CATALOG_TABLES_SQL = "('vehicle', 'vehicle_status', 'vehicle_qr', 'user', 'role')"


def list_field_permissions(role_id: int):
    return fetch_all(
        "SELECT id, table_name, field_name, access_level, description\n"
        "FROM vehicle_field_permission\n"
        "WHERE role_id = %s\n"
        "ORDER BY table_name, field_name",
        (role_id,),
    )


def list_field_permissions_admin():
    return fetch_all(
        "SELECT vfp.id, vfp.role_id, r.role_code, r.name_cn, r.name_jp,\n"
        "       vfp.table_name, vfp.field_name, vfp.access_level, vfp.description\n"
        "FROM vehicle_field_permission vfp\n"
        "JOIN role r ON vfp.role_id = r.id\n"
        "ORDER BY r.role_code, vfp.table_name, vfp.field_name"
    )


def field_permission_exists(role_id: int, table_name: str, field_name: str) -> bool:
    row = fetch_one(
        "SELECT id FROM vehicle_field_permission\n"
        "WHERE role_id = %s AND table_name = %s AND field_name = %s",
        (role_id, table_name, field_name),
    )
    return row is not None


def list_field_catalog():
    return fetch_all(
        "SELECT table_name, field_name\n"
        "FROM field_catalog\n"
        "WHERE field_name <> '__TABLE__'\n"
        "ORDER BY table_name, field_name"
    )


def refresh_field_catalog():
    execute(
        "DELETE fc FROM field_catalog fc\n"
        "LEFT JOIN information_schema.columns ic\n"
        "  ON fc.table_name = ic.table_name\n"
        "  AND fc.field_name = ic.column_name\n"
        "  AND ic.table_schema = DATABASE()\n"
        "WHERE fc.table_name IN " + CATALOG_TABLES_SQL + "\n"
        "  AND fc.field_name <> '__TABLE__'\n"
        "  AND ic.column_name IS NULL",
    )
    execute(
        "INSERT INTO field_catalog (table_name, field_name, data_type, is_nullable)\n"
        "SELECT table_name, column_name, data_type, (is_nullable = 'YES')\n"
        "FROM information_schema.columns\n"
        "WHERE table_schema = DATABASE()\n"
        "  AND table_name IN " + CATALOG_TABLES_SQL + "\n"
        "ON DUPLICATE KEY UPDATE\n"
        "  data_type = VALUES(data_type),\n"
        "  is_nullable = VALUES(is_nullable),\n"
        "  updated_at = CURRENT_TIMESTAMP",
    )
    execute(
        "INSERT INTO field_catalog (table_name, field_name, data_type, is_nullable, is_audited)\n"
        "SELECT table_name, '__TABLE__', 'table', 0, 1\n"
        "FROM information_schema.tables\n"
        "WHERE table_schema = DATABASE()\n"
        "  AND table_name IN " + CATALOG_TABLES_SQL + "\n"
        "ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP",
    )


def upsert_field_permission(
    role_id: int,
    table_name: str,
    field_name: str,
    access_level: int,
    description: str,
):
    execute(
        "INSERT INTO vehicle_field_permission\n"
        "(role_id, table_name, field_name, access_level, description)\n"
        "VALUES (%s, %s, %s, %s, %s)\n"
        "ON DUPLICATE KEY UPDATE\n"
        "    access_level = VALUES(access_level),\n"
        "    description = VALUES(description),\n"
        "    updated_at = CURRENT_TIMESTAMP",
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
        "UPDATE vehicle_field_permission\n"
        "SET role_id = %s,\n"
        "    table_name = %s,\n"
        "    field_name = %s,\n"
        "    access_level = %s,\n"
        "    description = %s\n"
        "WHERE id = %s",
        (role_id, table_name, field_name, access_level, description, permission_id),
    )


def delete_field_permission(role_id: int, table_name: str, field_name: str):
    execute(
        "DELETE FROM vehicle_field_permission\n"
        "WHERE role_id = %s AND table_name = %s AND field_name = %s",
        (role_id, table_name, field_name),
    )
