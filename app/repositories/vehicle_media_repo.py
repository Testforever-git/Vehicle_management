from typing import Optional

import mysql.connector

from app.db.mysql import fetch_all, execute

_MEDIA_TABLE_AVAILABLE: Optional[bool] = None
_MEDIA_COLUMNS: Optional[set[str]] = None


def _vehicle_media_table_exists() -> bool:
    global _MEDIA_TABLE_AVAILABLE
    if _MEDIA_TABLE_AVAILABLE is not None:
        return _MEDIA_TABLE_AVAILABLE
    try:
        row = fetch_all("SHOW TABLES LIKE %s", ("vehicle_media",))
        _MEDIA_TABLE_AVAILABLE = bool(row)
    except mysql.connector.Error:
        _MEDIA_TABLE_AVAILABLE = False
    return _MEDIA_TABLE_AVAILABLE


def _vehicle_media_columns() -> set[str]:
    global _MEDIA_COLUMNS
    if _MEDIA_COLUMNS is not None:
        return _MEDIA_COLUMNS
    if not _vehicle_media_table_exists():
        _MEDIA_COLUMNS = set()
        return _MEDIA_COLUMNS
    try:
        rows = fetch_all("SHOW COLUMNS FROM vehicle_media")
        _MEDIA_COLUMNS = {row["Field"] for row in rows}
    except mysql.connector.Error:
        _MEDIA_COLUMNS = set()
    return _MEDIA_COLUMNS


def list_vehicle_media(vehicle_id: int, file_type: str):
    if not _vehicle_media_table_exists():
        return []
    columns = ["id", "vehicle_id", "file_type", "file_path"]
    available = _vehicle_media_columns()
    for optional in ["description", "uploaded_by", "uploaded_at"]:
        if optional in available:
            columns.append(optional)
    return fetch_all(
        """
        SELECT {columns}
        FROM vehicle_media
        WHERE vehicle_id = %s AND file_type = %s
        ORDER BY id
        """.format(columns=", ".join(columns)),
        (vehicle_id, file_type),
    )


def create_vehicle_media(vehicle_id: int, file_type: str, file_paths: list[str], uploaded_by: Optional[int]):
    if not _vehicle_media_table_exists():
        return 0
    available = _vehicle_media_columns()
    columns = ["vehicle_id", "file_type", "file_path"]
    value_placeholders = ["%s", "%s", "%s"]
    include_uploaded_by = "uploaded_by" in available
    include_uploaded_at = "uploaded_at" in available
    if include_uploaded_by:
        columns.append("uploaded_by")
        value_placeholders.append("%s")
    for path in file_paths:
        params = [vehicle_id, file_type, path]
        if include_uploaded_by:
            params.append(uploaded_by)
        placeholders = ", ".join(value_placeholders)
        values_sql = f"{placeholders}{', NOW()' if include_uploaded_at else ''}"
        insert_columns = ", ".join(columns + (["uploaded_at"] if include_uploaded_at else []))
        execute(
            f"""
            INSERT INTO vehicle_media ({insert_columns})
            VALUES ({values_sql})
            """,
            tuple(params),
        )


def delete_vehicle_media(vehicle_id: int, file_type: str, file_paths: list[str]):
    if not _vehicle_media_table_exists():
        return 0
    for path in file_paths:
        execute(
            """
            DELETE FROM vehicle_media
            WHERE vehicle_id = %s AND file_type = %s AND file_path = %s
            """,
            (vehicle_id, file_type, path),
        )


def update_vehicle_media_paths(vehicle_id: int, old_prefix: str, new_prefix: str):
    if not _vehicle_media_table_exists():
        return 0
    execute(
        """
        UPDATE vehicle_media
        SET file_path = REPLACE(file_path, %s, %s)
        WHERE vehicle_id = %s
        """,
        (old_prefix, new_prefix, vehicle_id),
    )
