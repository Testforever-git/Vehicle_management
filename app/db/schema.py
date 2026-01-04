from werkzeug.security import generate_password_hash

from .mysql import execute, fetch_one


def ensure_schema():
    _create_tables()
    _create_views()
    _seed_roles()
    _seed_role_permissions()
    _seed_users()
    _seed_customers()
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
            is_audited TINYINT(1) NOT NULL DEFAULT 1,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_table_field (table_name, field_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    if not fetch_one(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'field_catalog'
          AND column_name = 'is_audited'
        """
    ):
        execute(
            """
            ALTER TABLE field_catalog
            ADD COLUMN is_audited TINYINT(1) NOT NULL DEFAULT 1
            """
        )

    execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            vehicle_id INT NULL,
            actor ENUM('user','system') NOT NULL DEFAULT 'system',
            actor_id INT NULL,
            action_type ENUM('login','logout','insert','delete','update') NOT NULL,
            action_detail JSON NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_audit_created_at (created_at),
            KEY idx_audit_vehicle_id (vehicle_id),
            KEY idx_audit_actor (actor, actor_id),
            KEY idx_audit_action_type (action_type, created_at),
            CONSTRAINT fk_audit_vehicle
              FOREIGN KEY (vehicle_id) REFERENCES vehicle(id)
              ON UPDATE CASCADE
              ON DELETE SET NULL,
            CONSTRAINT fk_audit_actor_user
              FOREIGN KEY (actor_id) REFERENCES user(id)
              ON UPDATE CASCADE
              ON DELETE SET NULL,
            CONSTRAINT chk_audit_action_detail_json
              CHECK (JSON_VALID(action_detail))
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

    execute(
        """
        CREATE TABLE IF NOT EXISTS customer (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          customer_no VARCHAR(32) NOT NULL COMMENT '客户编号(业务展示用，可用规则生成)',
          customer_type ENUM('personal','company') NOT NULL DEFAULT 'personal',
          display_name VARCHAR(128) DEFAULT NULL,
          full_name VARCHAR(128) DEFAULT NULL,
          full_name_kana VARCHAR(128) DEFAULT NULL,
          birthday DATE DEFAULT NULL,
          gender ENUM('unknown','male','female','other') NOT NULL DEFAULT 'unknown',
          status ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active',
          last_login_at DATETIME DEFAULT NULL,
          created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_customer_no (customer_no),
          KEY idx_customer_type (customer_type),
          KEY idx_customer_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS customer_auth_identity (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          customer_id BIGINT UNSIGNED NOT NULL,
          identity_type ENUM('email','phone','oauth') NOT NULL,
          identifier VARCHAR(255) NOT NULL COMMENT '邮箱/手机号/三方openid等',
          is_primary TINYINT(1) NOT NULL DEFAULT 0,
          verified_at DATETIME DEFAULT NULL,
          provider VARCHAR(32) DEFAULT NULL COMMENT 'oauth provider: google/apple/line等',
          provider_uid VARCHAR(255) DEFAULT NULL COMMENT 'provider user id',
          created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_identity (identity_type, identifier),
          KEY idx_customer_id (customer_id),
          KEY idx_customer_primary (customer_id, is_primary),
          CONSTRAINT fk_customer_auth_identity_customer
            FOREIGN KEY (customer_id) REFERENCES customer(id)
            ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS store (
          id INT NOT NULL AUTO_INCREMENT,
          name VARCHAR(64) NOT NULL,
          address_jp VARCHAR(255) NOT NULL,
          postcode VARCHAR(16) DEFAULT NULL,
          lat DECIMAL(10,7) DEFAULT NULL,
          lng DECIMAL(10,7) DEFAULT NULL,
          phone VARCHAR(32) DEFAULT NULL,
          is_active TINYINT(1) NOT NULL DEFAULT 1,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uk_store_name (name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    if fetch_one(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'vehicle'
        """
    ) and not fetch_one(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'vehicle'
          AND column_name = 'garage_store_id'
        """
    ):
        execute(
            """
            ALTER TABLE vehicle
            ADD COLUMN garage_store_id INT DEFAULT NULL
            """
        )
        execute(
            """
            ALTER TABLE vehicle
            ADD KEY idx_vehicle_garage_store_id (garage_store_id)
            """
        )
        execute(
            """
            ALTER TABLE vehicle
            ADD CONSTRAINT fk_vehicle_garage_store
              FOREIGN KEY (garage_store_id) REFERENCES store(id)
              ON DELETE SET NULL ON UPDATE CASCADE
            """
        )

    execute(
        """
        CREATE TABLE IF NOT EXISTS rental_vehicle_pricing (
          vehicle_id INT NOT NULL,
          currency CHAR(3) NOT NULL DEFAULT 'JPY',
          daily_price INT NOT NULL,
          deposit_amount INT NOT NULL DEFAULT 0,
          insurance_per_day INT NOT NULL DEFAULT 0,
          free_km_per_day INT DEFAULT NULL,
          extra_km_price INT DEFAULT NULL,
          cleaning_fee INT NOT NULL DEFAULT 0,
          late_fee_per_day INT NOT NULL DEFAULT 0,
          tax_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          updated_by INT DEFAULT NULL,
          PRIMARY KEY (vehicle_id),
          CONSTRAINT fk_pricing_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE,
          CONSTRAINT fk_pricing_updated_by FOREIGN KEY (updated_by) REFERENCES user(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS rental_longterm_discount_rule (
          id INT NOT NULL AUTO_INCREMENT,
          vehicle_id INT NOT NULL,
          min_days INT NOT NULL,
          max_days INT DEFAULT NULL,
          discount_type ENUM('percent','amount') NOT NULL,
          discount_value INT NOT NULL,
          priority INT NOT NULL DEFAULT 100,
          is_active TINYINT(1) NOT NULL DEFAULT 1,
          valid_from DATE DEFAULT NULL,
          valid_to DATE DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_discount_vehicle_days (vehicle_id, min_days, max_days, is_active),
          CONSTRAINT fk_discount_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS rental_service_catalog (
          id INT NOT NULL AUTO_INCREMENT,
          code VARCHAR(32) NOT NULL,
          name_jp VARCHAR(64) NOT NULL,
          name_cn VARCHAR(64) NOT NULL,
          pricing_type ENUM('per_booking','per_day','per_hour','per_unit') NOT NULL,
          price INT NOT NULL,
          currency CHAR(3) NOT NULL DEFAULT 'JPY',
          is_active TINYINT(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (id),
          UNIQUE KEY uk_service_code (code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS rental_delivery_fee_tier (
          id INT NOT NULL AUTO_INCREMENT,
          min_km DECIMAL(8,2) NOT NULL,
          max_km DECIMAL(8,2) DEFAULT NULL,
          fee_amount INT NOT NULL,
          currency CHAR(3) NOT NULL DEFAULT 'JPY',
          is_active TINYINT(1) NOT NULL DEFAULT 1,
          PRIMARY KEY (id),
          KEY idx_delivery_fee_km (min_km, max_km, is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS rental_booking (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          vehicle_id INT NOT NULL,
          customer_id BIGINT UNSIGNED NOT NULL,
          start_date DATE NOT NULL,
          end_date DATE NOT NULL,
          pickup_method ENUM('store','address') NOT NULL,
          pickup_store_id INT DEFAULT NULL,
          pickup_address VARCHAR(255) DEFAULT NULL,
          pickup_lat DECIMAL(10,7) DEFAULT NULL,
          pickup_lng DECIMAL(10,7) DEFAULT NULL,
          dropoff_method ENUM('store','address') NOT NULL,
          dropoff_store_id INT DEFAULT NULL,
          dropoff_address VARCHAR(255) DEFAULT NULL,
          dropoff_lat DECIMAL(10,7) DEFAULT NULL,
          dropoff_lng DECIMAL(10,7) DEFAULT NULL,
          price_snapshot JSON NOT NULL,
          access_token VARCHAR(64) NOT NULL,
          status ENUM('pending','awaiting_payment','confirmed','cancelled') NOT NULL DEFAULT 'pending',
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uk_booking_token (access_token),
          KEY idx_booking_vehicle (vehicle_id),
          KEY idx_booking_customer (customer_id),
          KEY idx_booking_status (status),
          CONSTRAINT fk_booking_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE,
          CONSTRAINT fk_booking_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE,
          CONSTRAINT fk_booking_pickup_store FOREIGN KEY (pickup_store_id) REFERENCES store(id) ON DELETE SET NULL,
          CONSTRAINT fk_booking_dropoff_store FOREIGN KEY (dropoff_store_id) REFERENCES store(id) ON DELETE SET NULL,
          CONSTRAINT chk_booking_price_snapshot_json CHECK (JSON_VALID(price_snapshot))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _create_views():
    execute(
        """
        CREATE OR REPLACE VIEW v_vehicle_i18n AS
        SELECT
          v.*,
          s.name AS store_name,
          b.brand_code,
          b.name_jp AS brand_jp,
          b.name_cn AS brand_cn,
          m.model_code,
          m.name_jp AS model_jp,
          m.name_cn AS model_cn,
          c.color_code,
          c.name_jp AS color_jp,
          c.name_cn AS color_cn,
          el.name_jp AS engine_layout_jp,
          el.name_cn AS engine_layout_cn,
          ft.name_jp AS fuel_type_jp,
          ft.name_cn AS fuel_type_cn,
          dt.name_jp AS drive_type_jp,
          dt.name_cn AS drive_type_cn
        FROM vehicle v
        JOIN md_brand b ON b.id = v.brand_id
        JOIN md_model m ON m.id = v.model_id
        LEFT JOIN md_color c ON c.id = v.color_id
        LEFT JOIN md_enum el ON el.enum_type='engine_layout'
          AND el.enum_code=v.engine_layout_code
          AND el.is_active=1
        LEFT JOIN md_enum ft ON ft.enum_type='fuel_type'
          AND ft.enum_code=v.fuel_type_code
          AND ft.is_active=1
        LEFT JOIN md_enum dt ON dt.enum_type='drive_type'
          AND dt.enum_code=v.drive_type_code
          AND dt.is_active=1
        LEFT JOIN store s ON s.id = v.garage_store_id
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


def _seed_customers():
    customers = [
        ("CUST-0001", "personal", "测试客户", "测试客户", "test@example.com", "+819012345678"),
    ]
    for customer_no, customer_type, display_name, full_name, email, phone in customers:
        execute(
            """
            INSERT IGNORE INTO customer
              (customer_no, customer_type, display_name, full_name, status)
            VALUES (%s, %s, %s, %s, 'active')
            """,
            (customer_no, customer_type, display_name, full_name),
        )
        row = fetch_one("SELECT id FROM customer WHERE customer_no = %s", (customer_no,))
        if row:
            execute(
                """
                INSERT IGNORE INTO customer_auth_identity
                  (customer_id, identity_type, identifier, is_primary, verified_at)
                VALUES (%s, 'email', %s, 1, NOW())
                """,
                (row["id"], email),
            )
            if phone:
                execute(
                    """
                    INSERT IGNORE INTO customer_auth_identity
                      (customer_id, identity_type, identifier, is_primary, verified_at)
                    VALUES (%s, 'phone', %s, 1, NOW())
                    """,
                    (row["id"], phone),
                )


def _seed_field_permissions():
    rules = [
        ("vehicle", "brand_id", "basic", False, "车辆品牌"),
        ("vehicle", "model_id", "basic", False, "车辆型号"),
        ("vehicle", "plate_no", "basic", False, "车牌号"),
        ("vehicle", "vin", "advanced", False, "VIN"),
        ("vehicle", "type_designation_code", "advanced", False, "型式指定番号"),
        ("vehicle", "garage_store_id", "advanced", True, "所属门店"),
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
