from ..db.mysql import execute, fetch_all
AUDIT_TABLES_SQL = "('vehicle', 'vehicle_status', 'user', 'role')"


def list_audit_catalog():
    return fetch_all(
        "SELECT table_name, field_name, is_audited\n"
        "FROM field_catalog\n"
        "WHERE table_name IN " + AUDIT_TABLES_SQL + "\n"
        "ORDER BY table_name, field_name"
    )


def get_audit_config(table_name: str) -> tuple[bool, set[str]]:
    rows = fetch_all(
        "SELECT field_name, is_audited\n"
        "FROM field_catalog\n"
        "WHERE table_name = %s",
        (table_name,),
    )
    table_audited = False
    audited_fields = set()
    for row in rows:
        field_name = row["field_name"]
        if field_name == "__TABLE__":
            table_audited = bool(row["is_audited"])
        elif row["is_audited"]:
            audited_fields.add(field_name)
    return table_audited, audited_fields


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
