from ..db.mysql import fetch_all, fetch_one, execute


def get_user_by_username(username: str):
    return fetch_one(
        """
        SELECT u.id, u.username, u.password_hash, u.full_name, u.is_active,
               u.is_deleted, u.expired_at,
               r.id AS role_id, r.role_code, r.name_cn, r.name_jp
        FROM `user` u
        JOIN role r ON u.role_id = r.id
        WHERE u.username = %s
          AND u.is_deleted = 0
          AND (u.expired_at IS NULL OR u.expired_at > NOW())
        """,
        (username,),
    )


def get_user_by_id(user_id: int):
    return fetch_one(
        """
        SELECT u.id, u.username, u.password_hash, u.full_name, u.is_active,
               u.is_deleted, u.expired_at,
               r.id AS role_id, r.role_code, r.name_cn, r.name_jp
        FROM `user` u
        JOIN role r ON u.role_id = r.id
        WHERE u.id = %s
          AND u.is_deleted = 0
          AND (u.expired_at IS NULL OR u.expired_at > NOW())
        """,
        (user_id,),
    )


def list_users():
    return fetch_all(
        """
        SELECT u.id, u.username, u.full_name, u.is_active,
               u.is_deleted, u.expired_at,
               r.id AS role_id, r.role_code, r.name_cn, r.name_jp
        FROM `user` u
        JOIN role r ON u.role_id = r.id
        WHERE u.is_deleted = 0
        ORDER BY u.id
        """
    )


def create_user(username: str, password_hash: str, role_id: int, full_name: str, is_active: bool):
    execute(
        """
        INSERT INTO `user` (username, password_hash, role_id, full_name, is_active, is_deleted)
        VALUES (%s, %s, %s, %s, %s, 0)
        """,
        (username, password_hash, role_id, full_name, int(is_active)),
    )


def update_user(user_id: int, role_id: int, is_active: bool, full_name: str):
    execute(
        """
        UPDATE `user`
        SET role_id = %s, is_active = %s, full_name = %s
        WHERE id = %s
        """,
        (role_id, int(is_active), full_name, user_id),
    )


def soft_delete_user(user_id: int):
    execute(
        """
        UPDATE `user`
        SET is_deleted = 1
        WHERE id = %s
        """,
        (user_id,),
    )


def update_password(user_id: int, password_hash: str):
    execute(
        """
        UPDATE `user`
        SET password_hash = %s
        WHERE id = %s
        """,
        (password_hash, user_id),
    )
