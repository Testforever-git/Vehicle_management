# app/repositories/master_data_repo.py
from app.db.mysql import fetch_all, fetch_one, execute


def list_brands():
    sql = """
    SELECT id, brand_code, name_cn, name_jp, is_active
    FROM md_brand
    ORDER BY id DESC
    """
    return fetch_all(sql)


def list_models():
    sql = """
    SELECT id, brand_id, model_code, name_cn, name_jp, is_active
    FROM md_model
    ORDER BY id DESC
    """
    return fetch_all(sql)


def list_colors():
    sql = """
    SELECT id, color_code, name_cn, name_jp, is_active
    FROM md_color
    ORDER BY id DESC
    """
    return fetch_all(sql)


def list_enums():
    sql = """
    SELECT id, enum_type, enum_code, name_cn, name_jp, is_active
    FROM md_enum
    ORDER BY enum_type, enum_code
    """
    return fetch_all(sql)


def create_brand(brand_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    INSERT INTO md_brand (brand_code, name_cn, name_jp, is_active)
    VALUES (%s, %s, %s, %s)
    """
    return execute(sql, (brand_code, name_cn, name_jp, 1 if is_active else 0))


def update_brand(brand_id: int, brand_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    UPDATE md_brand
    SET brand_code = %s, name_cn = %s, name_jp = %s, is_active = %s
    WHERE id = %s
    """
    return execute(sql, (brand_code, name_cn, name_jp, 1 if is_active else 0, brand_id))


def deactivate_brand(brand_id: int):
    sql = "UPDATE md_brand SET is_active = 0 WHERE id = %s"
    return execute(sql, (brand_id,))


def create_model(brand_id: int, model_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    INSERT INTO md_model (brand_id, model_code, name_cn, name_jp, is_active)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute(sql, (brand_id, model_code, name_cn, name_jp, 1 if is_active else 0))


def update_model(model_id: int, brand_id: int, model_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    UPDATE md_model
    SET brand_id = %s, model_code = %s, name_cn = %s, name_jp = %s, is_active = %s
    WHERE id = %s
    """
    return execute(sql, (brand_id, model_code, name_cn, name_jp, 1 if is_active else 0, model_id))


def deactivate_model(model_id: int):
    sql = "UPDATE md_model SET is_active = 0 WHERE id = %s"
    return execute(sql, (model_id,))


def create_color(color_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    INSERT INTO md_color (color_code, name_cn, name_jp, is_active)
    VALUES (%s, %s, %s, %s)
    """
    return execute(sql, (color_code, name_cn, name_jp, 1 if is_active else 0))


def update_color(color_id: int, color_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    UPDATE md_color
    SET color_code = %s, name_cn = %s, name_jp = %s, is_active = %s
    WHERE id = %s
    """
    return execute(sql, (color_code, name_cn, name_jp, 1 if is_active else 0, color_id))


def deactivate_color(color_id: int):
    sql = "UPDATE md_color SET is_active = 0 WHERE id = %s"
    return execute(sql, (color_id,))


def create_enum(enum_type: str, enum_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    INSERT INTO md_enum (enum_type, enum_code, name_cn, name_jp, is_active)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute(sql, (enum_type, enum_code, name_cn, name_jp, 1 if is_active else 0))


def update_enum(enum_id: int, enum_type: str, enum_code: str, name_cn: str, name_jp: str, is_active: bool):
    sql = """
    UPDATE md_enum
    SET enum_type = %s, enum_code = %s, name_cn = %s, name_jp = %s, is_active = %s
    WHERE id = %s
    """
    return execute(sql, (enum_type, enum_code, name_cn, name_jp, 1 if is_active else 0, enum_id))


def deactivate_enum(enum_id: int):
    sql = "UPDATE md_enum SET is_active = 0 WHERE id = %s"
    return execute(sql, (enum_id,))
