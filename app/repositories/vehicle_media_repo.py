from typing import Optional

from app.db.mysql import fetch_all, execute


def list_vehicle_media(vehicle_id: int, file_type: str):
    return fetch_all(
        """
        SELECT id, vehicle_id, file_type, file_path, description, uploaded_by, uploaded_at
        FROM vehicle_media
        WHERE vehicle_id = %s AND file_type = %s
        ORDER BY id
        """,
        (vehicle_id, file_type),
    )


def create_vehicle_media(vehicle_id: int, file_type: str, file_paths: list[str], uploaded_by: Optional[int]):
    for path in file_paths:
        execute(
            """
            INSERT INTO vehicle_media (vehicle_id, file_type, file_path, uploaded_by, uploaded_at)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (vehicle_id, file_type, path, uploaded_by),
        )


def delete_vehicle_media(vehicle_id: int, file_type: str, file_paths: list[str]):
    for path in file_paths:
        execute(
            """
            DELETE FROM vehicle_media
            WHERE vehicle_id = %s AND file_type = %s AND file_path = %s
            """,
            (vehicle_id, file_type, path),
        )


def update_vehicle_media_paths(vehicle_id: int, old_prefix: str, new_prefix: str):
    execute(
        """
        UPDATE vehicle_media
        SET file_path = REPLACE(file_path, %s, %s)
        WHERE vehicle_id = %s
        """,
        (old_prefix, new_prefix, vehicle_id),
    )
