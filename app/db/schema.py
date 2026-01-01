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
            role_id INT NOT NULL,
            table_name VARCHAR(64) NOT NULL,
            field_name VARCHAR(64) NOT NULL,
            access_level INT NOT NULL,
            description VARCHAR(255),
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_role_table_field (role_id, table_name, field_name),
            KEY idx_role_id (role_id),
            CONSTRAINT fk_vfp_role FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS field_catalog (
            id INT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(64) NOT NULL,
            field_name VARCHAR(64) NOT NULL,
            data_type VARCHAR(64) NOT NULL,
            is_nullable TINYINT(1) NOT NULL,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_table_field (table_name, field_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_qr (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_id INT NOT NULL,
            qr_slug VARCHAR(64) NOT NULL UNIQUE,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_vehicle_qr_vehicle_id (vehicle_id),
            CONSTRAINT fk_vehicle_qr_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE
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
        ("vehicle", "brand_id", "basic", False, "车辆品牌"),
        ("vehicle", "model_id", "basic", False, "车辆型号"),
        ("vehicle", "plate_no", "basic", False, "车牌号"),
        ("vehicle", "vin", "advanced", False, "VIN"),
        ("vehicle", "type_designation_code", "advanced", False, "型式指定番号"),
        ("vehicle", "garage_name", "advanced", True, "车库名称"),
        ("vehicle", "garage_address_jp", "advanced", True, "车库地址"),
        ("vehicle", "purchase_price", "admin", True, "购入价格"),
        ("vehicle", "legal_doc", "advanced", False, "证件目录"),
        ("vehicle", "vehicle_photo", "advanced", False, "车辆照片目录"),
        ("vehicle_status", "status", "basic", False, "状态"),
        ("vehicle_status", "mileage", "advanced", False, "里程"),
        ("vehicle_status", "fuel_level", "advanced", False, "油量"),
        ("vehicle_status", "location_desc", "advanced", False, "位置描述"),
    ]

    role_order = ["user", "engineer", "admin"]
    for table_name, field_name, level, editable, description in rules:
        start_index = role_order.index(_min_role_for_level(level))
        access_level = 20 if editable else 10
        for role_code in role_order[start_index:]:
            role_id = _role_id(role_code)
            if not role_id:
                continue
            execute(
                """
                INSERT IGNORE INTO vehicle_field_permission
                (role_id, table_name, field_name, access_level, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (role_id, table_name, field_name, access_level, description),
            )


def _min_role_for_level(level: str) -> str:
    if level == "basic":
        return "user"
    if level == "advanced":
        return "engineer"
    return "admin"
