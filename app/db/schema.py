from werkzeug.security import generate_password_hash

from .mysql import execute, fetch_one


def ensure_schema():
    _create_tables()
    _seed_roles()
    _seed_role_permissions()
    _seed_users()
    _seed_field_permissions()


def _create_tables():
    execute(
        """
        CREATE TABLE IF NOT EXISTS role (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role_code VARCHAR(32) NOT NULL UNIQUE,
            name_cn VARCHAR(64),
            name_jp VARCHAR(64),
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS `user` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role_id INT NOT NULL,
            full_name VARCHAR(128),
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_role_id (role_id),
            CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES role(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS role_permission (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role_id INT NOT NULL,
            module_name VARCHAR(64) NOT NULL,
            permission_type VARCHAR(64) NOT NULL,
            allow_flag TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_role_permission (role_id, module_name, permission_type),
            CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES role(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_field_permission (
            id INT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(64) NOT NULL,
            field_name VARCHAR(64) NOT NULL,
            access_level VARCHAR(32) NOT NULL,
            min_role_code VARCHAR(32) NOT NULL,
            is_visible TINYINT(1) NOT NULL DEFAULT 1,
            is_editable TINYINT(1) NOT NULL DEFAULT 0,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_table_field (table_name, field_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _seed_roles():
    roles = [
        ("user", "普通用户", "一般ユーザー", "Basic user"),
        ("engineer", "工程师", "エンジニア", "Engineer"),
        ("admin", "管理员", "管理者", "Administrator"),
    ]
    for code, name_cn, name_jp, desc in roles:
        execute(
            """
            INSERT IGNORE INTO role (role_code, name_cn, name_jp, description)
            VALUES (%s, %s, %s, %s)
            """,
            (code, name_cn, name_jp, desc),
        )


def _role_id(role_code: str):
    row = fetch_one("SELECT id FROM role WHERE role_code = %s", (role_code,))
    return row["id"] if row else None


def _seed_role_permissions():
    role_permissions = {
        "user": [
            ("dashboard", "view"),
            ("vehicle", "view"),
        ],
        "engineer": [
            ("dashboard", "view"),
            ("vehicle", "view"),
            ("vehicle", "edit"),
            ("status", "view"),
            ("vehicle_qr", "view"),
        ],
        "admin": [
            ("dashboard", "view"),
            ("vehicle", "view"),
            ("vehicle", "edit"),
            ("vehicle", "export"),
            ("status", "view"),
            ("vehicle_qr", "view"),
            ("admin", "view"),
            ("admin", "edit"),
        ],
    }

    for role_code, perms in role_permissions.items():
        role_id = _role_id(role_code)
        if not role_id:
            continue
        for module_name, permission_type in perms:
            execute(
                """
                INSERT IGNORE INTO role_permission (role_id, module_name, permission_type, allow_flag)
                VALUES (%s, %s, %s, 1)
                """,
                (role_id, module_name, permission_type),
            )


def _seed_users():
    default_users = [
        ("admin", "管理员", "admin", "Admin123!"),
        ("engineer", "工程师", "engineer", "Engineer123!"),
        ("user", "普通用户", "user", "User123!"),
    ]
    for role_code, full_name, username, password in default_users:
        role_id = _role_id(role_code)
        if not role_id:
            continue
        password_hash = generate_password_hash(password)
        execute(
            """
            INSERT IGNORE INTO `user` (username, password_hash, role_id, full_name, is_active)
            VALUES (%s, %s, %s, %s, 1)
            """,
            (username, password_hash, role_id, full_name),
        )


def _seed_field_permissions():
    rules = [
        ("vehicle", "brand_jp", "basic", False, "车辆品牌(日文)"),
        ("vehicle", "model_jp", "basic", False, "车辆型号(日文)"),
        ("vehicle", "plate_no", "basic", False, "车牌号"),
        ("vehicle", "vin", "advanced", False, "VIN"),
        ("vehicle", "type_designation_code", "advanced", False, "型式指定番号"),
        ("vehicle", "garage_name", "advanced", True, "车库名称"),
        ("vehicle", "garage_address_jp", "advanced", True, "车库地址"),
        ("vehicle", "purchase_price", "admin", True, "购入价格"),
        ("vehicle", "legal_doc_dir", "advanced", False, "证件目录"),
        ("vehicle", "vehicle_photo_dir", "advanced", False, "车辆照片目录"),
        ("vehicle_status", "status", "basic", False, "状态"),
        ("vehicle_status", "mileage", "advanced", False, "里程"),
        ("vehicle_status", "fuel_level", "advanced", False, "油量"),
        ("vehicle_status", "location_desc", "advanced", False, "位置描述"),
    ]

    for table_name, field_name, level, editable, description in rules:
        min_role_code = _min_role_for_level(level)
        execute(
            """
            INSERT IGNORE INTO vehicle_field_permission
            (table_name, field_name, access_level, min_role_code, is_visible, is_editable, description)
            VALUES (%s, %s, %s, %s, 1, %s, %s)
            """,
            (table_name, field_name, level, min_role_code, int(editable), description),
        )


def _min_role_for_level(level: str) -> str:
    if level == "basic":
        return "user"
    if level == "advanced":
        return "engineer"
    return "admin"
