from ..db.mysql import execute, fetch_all
from .field_permission_repo import CATALOG_TABLES_SQL


def list_audit_catalog():
    return fetch_all(
        "SELECT table_name, field_name, is_audited\n"
        "FROM field_catalog\n"
        "WHERE table_name IN " + CATALOG_TABLES_SQL + "\n"
        "ORDER BY table_name, field_name"
    )


def update_audit_flags(table_name: str, field_names: list[str], is_audited: bool):
    if not field_names:
        return
    placeholders = ", ".join(["%s"] * len(field_names))
    sql = (
        "UPDATE field_catalog\n"
        "SET is_audited = %s, updated_at = CURRENT_TIMESTAMP\n"
        f"WHERE table_name = %s AND field_name IN ({placeholders})"
    )
    execute(sql, (int(is_audited), table_name, *field_names))


def update_table_audit_flag(table_name: str, is_audited: bool):
    execute(
        "UPDATE field_catalog\n"
        "SET is_audited = %s, updated_at = CURRENT_TIMESTAMP\n"
        "WHERE table_name = %s AND field_name = '__TABLE__'",
        (int(is_audited), table_name),
    )
