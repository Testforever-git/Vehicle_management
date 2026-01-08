# app/repositories/vehicle_feature_repo.py
from app.db.mysql import fetch_all, execute


def list_vehicle_feature_values(vehicle_id: int):
    sql = """
    SELECT feature_code, value_bool, value_enum, value_int, value_text
    FROM vehicle_feature_value
    WHERE vehicle_id = %s
    """
    return fetch_all(sql, (vehicle_id,))


def upsert_vehicle_feature_value(
    vehicle_id: int,
    feature_code: str,
    value_bool: int | None,
    value_enum: str | None,
    value_int: int | None,
    value_text: str | None,
    updated_by: int | None,
    source: str = "manual",
):
    sql = """
    INSERT INTO vehicle_feature_value
      (vehicle_id, feature_code, value_bool, value_enum, value_int, value_text, source, updated_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
      value_bool = VALUES(value_bool),
      value_enum = VALUES(value_enum),
      value_int = VALUES(value_int),
      value_text = VALUES(value_text),
      source = VALUES(source),
      updated_by = VALUES(updated_by),
      updated_at = CURRENT_TIMESTAMP
    """
    return execute(
        sql,
        (
            vehicle_id,
            feature_code,
            value_bool,
            value_enum,
            value_int,
            value_text,
            source,
            updated_by,
        ),
    )


def delete_vehicle_feature_value(vehicle_id: int, feature_code: str):
    sql = """
    DELETE FROM vehicle_feature_value
    WHERE vehicle_id = %s AND feature_code = %s
    """
    return execute(sql, (vehicle_id, feature_code))
