import json

from app.db.mysql import fetch_all, fetch_one, execute


def list_feature_catalog(include_inactive: bool = False):
    where_sql = "" if include_inactive else "WHERE is_active = 1"
    return fetch_all(
        f"""
        SELECT
          code,
          name_jp,
          name_cn,
          value_type,
          enum_options_json,
          category_code,
          is_active,
          created_at,
          updated_at
        FROM feature_catalog
        {where_sql}
        ORDER BY category_code ASC, code ASC
        """
    )


def get_feature_catalog(code: str):
    return fetch_one(
        """
        SELECT
          code,
          name_jp,
          name_cn,
          value_type,
          enum_options_json,
          category_code,
          is_active,
          created_at,
          updated_at
        FROM feature_catalog
        WHERE code = %s
        """,
        (code,),
    )


def upsert_feature_catalog(
    code: str,
    name_jp: str,
    name_cn: str,
    value_type: str,
    enum_options: list | None,
    category_code: str | None,
    is_active: bool = True,
):
    enum_json = json.dumps(enum_options, ensure_ascii=False) if enum_options is not None else None
    execute(
        """
        INSERT INTO feature_catalog (
          code, name_jp, name_cn, value_type, enum_options_json, category_code, is_active
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
          name_jp = VALUES(name_jp),
          name_cn = VALUES(name_cn),
          value_type = VALUES(value_type),
          enum_options_json = VALUES(enum_options_json),
          category_code = VALUES(category_code),
          is_active = VALUES(is_active)
        """,
        (
            code,
            name_jp,
            name_cn,
            value_type,
            enum_json,
            category_code,
            int(is_active),
        ),
    )
