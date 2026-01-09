# app/repositories/feature_catalog_repo.py
from app.db.mysql import fetch_all, execute


def list_feature_catalog(include_inactive: bool = False):
    sql = """
    SELECT code, name_jp, name_cn, value_type, enum_options_json, category_code, is_active
    FROM feature_catalog
    """
    params = []
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY category_code, code"
    return fetch_all(sql, tuple(params))


def create_feature_catalog(
    code: str,
    name_jp: str,
    name_cn: str,
    value_type: str,
    enum_options_json: str | None,
    category_code: str | None,
    is_active: bool,
):
    sql = """
    INSERT INTO feature_catalog
    (code, name_jp, name_cn, value_type, enum_options_json, category_code, is_active)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return execute(
        sql,
        (
            code,
            name_jp,
            name_cn,
            value_type,
            enum_options_json,
            category_code,
            1 if is_active else 0,
        ),
    )


def update_feature_catalog(
    code: str,
    name_jp: str,
    name_cn: str,
    value_type: str,
    enum_options_json: str | None,
    category_code: str | None,
    is_active: bool,
):
    sql = """
    UPDATE feature_catalog
    SET name_jp = %s,
        name_cn = %s,
        value_type = %s,
        enum_options_json = %s,
        category_code = %s,
        is_active = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE code = %s
    """
    return execute(
        sql,
        (
            name_jp,
            name_cn,
            value_type,
            enum_options_json,
            category_code,
            1 if is_active else 0,
            code,
        ),
    )


def deactivate_feature_catalog(code: str):
    sql = "UPDATE feature_catalog SET is_active = 0 WHERE code = %s"
    return execute(sql, (code,))
