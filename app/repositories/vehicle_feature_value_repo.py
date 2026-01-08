from app.db.mysql import fetch_all, execute


def list_vehicle_feature_values(vehicle_id: int):
    return fetch_all(
        """
        SELECT
          fc.code,
          fc.name_jp,
          fc.name_cn,
          fc.value_type,
          fc.enum_options_json,
          fc.category_code,
          fc.is_active,
          vfv.value_bool,
          vfv.value_enum,
          vfv.value_int,
          vfv.value_text,
          vfv.source,
          vfv.updated_by,
          vfv.updated_at
        FROM feature_catalog fc
        LEFT JOIN vehicle_feature_value vfv
          ON vfv.feature_code = fc.code
          AND vfv.vehicle_id = %s
        WHERE fc.is_active = 1
        ORDER BY fc.category_code ASC, fc.code ASC
        """,
        (vehicle_id,),
    )


def replace_vehicle_feature_values(vehicle_id: int, rows: list[dict]):
    execute(
        """
        DELETE FROM vehicle_feature_value
        WHERE vehicle_id = %s
        """,
        (vehicle_id,),
    )
    if not rows:
        return
    for row in rows:
        execute(
            """
            INSERT INTO vehicle_feature_value (
              vehicle_id, feature_code, value_bool, value_enum, value_int, value_text, source, updated_by
            ) VALUES (
              %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                vehicle_id,
                row["feature_code"],
                row.get("value_bool"),
                row.get("value_enum"),
                row.get("value_int"),
                row.get("value_text"),
                row.get("source", "manual"),
                row.get("updated_by"),
            ),
        )
