-- Vehicle System Database Schema (V7)

-- 1. vehicle table: 静态车辆信息
CREATE TABLE IF NOT EXISTS vehicle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT UNIQUE,
    plate_no TEXT UNIQUE,
    brand_cn TEXT,
    brand_jp TEXT,
    model_cn TEXT,
    model_jp TEXT,
    color_cn TEXT,
    color_jp TEXT,
    model_year INTEGER,
    type_designation_code TEXT, -- 型式指定番号
    classification_number TEXT, -- 類別区分番号
    engine_code TEXT,
    engine_layout TEXT,
    displacement_cc INTEGER,
    fuel_type TEXT,
    drive_type TEXT,
    transmission TEXT,
    ownership_type TEXT,
    owner_id INTEGER,
    driver_id INTEGER,
    garage_name TEXT,
    garage_address_jp TEXT,
    garage_address_cn TEXT,
    garage_postcode TEXT,
    garage_lat REAL,
    garage_lng REAL,
    purchase_date DATE,
    purchase_price DECIMAL(10, 2),
    ext_json TEXT, -- 扩展字段
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. vehicle_status table: 动态车辆状态
CREATE TABLE IF NOT EXISTS vehicle_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('available', 'rented', 'maintenance', 'reserved', 'inactive')),
    mileage INTEGER,
    fuel_level INTEGER,
    speed INTEGER,
    engine_on BOOLEAN DEFAULT FALSE,
    alcohol_check_passed BOOLEAN DEFAULT NULL,
    location_lat REAL,
    location_lng REAL,
    location_desc TEXT,
    update_source TEXT CHECK(update_source IN ('manual', 'rental', 'maintenance', 'gps', 'alcohol_check', 'system')),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    ext_json TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(id),
    UNIQUE(vehicle_id)
);

-- 3. vehicle_media table: 附件/文件
CREATE TABLE IF NOT EXISTS vehicle_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    file_type TEXT,
    file_path TEXT,
    description TEXT,
    uploaded_by INTEGER,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(id)
);

-- 4. vehicle_log table: 操作与事件审计
CREATE TABLE IF NOT EXISTS vehicle_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    actor TEXT, -- user/system
    action_type TEXT,
    action_detail TEXT, -- JSON
    source_module TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(id)
);

-- 5. vehicle_qr table: 二维码入口
CREATE TABLE IF NOT EXISTS vehicle_qr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    qr_slug TEXT UNIQUE,
    qr_scope TEXT CHECK(qr_scope IN ('public', 'detail', 'edit', 'custom')),
    token_signature TEXT,
    expired_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    generated_by INTEGER, -- FK -> user.id
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(id)
);

-- 6. vehicle_field_permission table: 字段级权限配置
CREATE TABLE IF NOT EXISTS vehicle_field_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    field_name TEXT,
    access_level TEXT CHECK(access_level IN ('basic', 'advanced', 'admin')),
    min_role_code TEXT,
    is_visible BOOLEAN DEFAULT TRUE,
    is_editable BOOLEAN DEFAULT FALSE,
    description TEXT,
    UNIQUE(table_name, field_name)
);

-- 7. user table: 后台用户
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    role_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. role table: 角色
CREATE TABLE IF NOT EXISTS role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT UNIQUE,
    name_cn TEXT,
    name_jp TEXT
);

-- 9. role_permission table: 角色权限
CREATE TABLE IF NOT EXISTS role_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    module_name TEXT,
    permission_type TEXT,
    allow_flag BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (role_id) REFERENCES role(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vehicle_vin ON vehicle(vin);
CREATE INDEX IF NOT EXISTS idx_vehicle_plate ON vehicle(plate_no);
CREATE INDEX IF NOT EXISTS idx_vehicle_status_vehicle_id ON vehicle_status(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_media_vehicle_id ON vehicle_media(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_log_vehicle_id ON vehicle_log(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_qr_slug ON vehicle_qr(qr_slug);
CREATE INDEX IF NOT EXISTS idx_vehicle_log_created_at ON vehicle_log(created_at);