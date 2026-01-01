# Vehicle System — DB Schema (V7)

> 单一真相：本文档是车辆系统数据库结构的唯一依据。  
> 修改任何表结构必须先更新本文档，再改代码。

## 0. Version
- Version: V7
- Status: Frozen (可开发)
- Last Updated: 2025-XX-XX

## 1. Table Overview
- vehicle：车辆静态主数据（身份证）
- vehicle_status：车辆动态状态（里程/油量/位置/状态）
- vehicle_media：附件/文件
- vehicle_log：操作与事件审计
- vehicle_qr：二维码入口（public/detail/edit）
- vehicle_field_permission：字段级权限配置
- user / role / role_permission：后台用户与角色权限（RBAC）

## 2. vehicle
### Purpose
静态信息，不应频繁变动。租赁/维修不得直接污染 vehicle。

### Key Constraints
- UNIQUE(vin)

### Fields (summary)
 vehicle | CREATE TABLE `vehicle` (
  `id` int NOT NULL AUTO_INCREMENT,
  `brand_id` int NOT NULL,
  `model_id` int NOT NULL,
  `color_id` int DEFAULT NULL,
  `model_year_ad` smallint unsigned DEFAULT NULL COMMENT 'Gregorian year, e.g. 2021',
  `model_year_era` varchar(16) DEFAULT NULL COMMENT 'showa/heisei/reiwa',
  `model_year_era_year` smallint unsigned DEFAULT NULL COMMENT 'e.g. reiwa 3 -> 3',
  `plate_no` varchar(64) DEFAULT NULL,
  `vin` varchar(64) NOT NULL,
  `type_designation_code` varchar(64) DEFAULT NULL,
  `classification_number` varchar(32) DEFAULT NULL,
  `engine_code` varchar(32) DEFAULT NULL,
  `engine_layout_code` varchar(32) DEFAULT NULL,
  `displacement_cc` int unsigned DEFAULT NULL,
  `fuel_type_code` varchar(32) DEFAULT NULL,
  `drive_type_code` varchar(32) DEFAULT NULL,
  `transmission` varchar(32) DEFAULT NULL,
  `ownership_type` varchar(32) DEFAULT NULL,
  `owner_id` bigint unsigned DEFAULT NULL,
  `driver_id` bigint unsigned DEFAULT NULL,
  `garage_name` varchar(128) DEFAULT NULL,
  `garage_address_jp` varchar(255) DEFAULT NULL,
  `garage_address_cn` varchar(255) DEFAULT NULL,
  `garage_postcode` varchar(16) DEFAULT NULL,
  `garage_lat` decimal(10,7) DEFAULT NULL,
  `garage_lng` decimal(10,7) DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `purchase_price` bigint unsigned DEFAULT NULL,
  `legal_doc` varchar(255) DEFAULT NULL,
  `vehicle_photo` varchar(255) DEFAULT NULL,
  `ext_json` json DEFAULT NULL,
  `note` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_vehicle_vin` (`vin`),
  KEY `idx_vehicle_plate_no` (`plate_no`),
  KEY `fk_vehicle_updated_by` (`updated_by`),
  KEY `idx_vehicle_brand_id` (`brand_id`),
  KEY `idx_vehicle_model_id` (`model_id`),
  KEY `idx_vehicle_color_id` (`color_id`),
  CONSTRAINT `fk_vehicle_brand` FOREIGN KEY (`brand_id`) REFERENCES `md_brand` (`id`),
  CONSTRAINT `fk_vehicle_color` FOREIGN KEY (`color_id`) REFERENCES `md_color` (`id`),
  CONSTRAINT `fk_vehicle_model` FOREIGN KEY (`model_id`) REFERENCES `md_model` (`id`),
  CONSTRAINT `fk_vehicle_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `chk_model_year_era_year` CHECK (((`model_year_era_year` is null) or (`model_year_era_year` between 1 and 99)))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

2.1 Master Data（主数据/字典）规则
md_brand（品牌）
brand_code 为稳定代码（小写、无空格，如 tesla）
name_jp/name_cn 用于 UI 显示
停用品牌：is_active=0（不删除，以免历史数据失效）

md_model（车型）
(brand_id, model_code) 唯一
车型必须属于一个品牌（FK）
停用车型：is_active=0
md_color（颜色）
color_code 为稳定代码（如 white/black/silver）

停用颜色：is_active=0
md_enum（枚举字典）
enum_type 限定取值：engine_layout / fuel_type / drive_type
enum_code 为稳定代码（如 bev/awd/FF）
UI 显示使用 name_jp/name_cn

业务表不存多语言文本，只存 id/code，所有多语言通过 join 获取。

2.2 vehicle（车辆）规则
存储规则
brand_id：FK -> md_brand.id
model_id：FK -> md_model.id
color_id：FK -> md_color.id（可为空）
engine_layout_code：引用 md_enum(enum_type='engine_layout')
fuel_type_code：引用 md_enum(enum_type='fuel_type')
drive_type_code：引用 md_enum(enum_type='drive_type')

2.3 年份规则
model_year_ad：公历年份（统计/排序用）
model_year_era：年号（showa/heisei/reiwa）
model_year_era_year：年号年（1~99）
录入可只填其中一套，推荐录入时：输入和历则自动换算并写入 model_year_ad

2.4 查询显示（中日双语）
显示品牌：join md_brand
显示车型：join md_model
显示颜色：join md_color
显示枚举：join md_enum（按 enum_type + code）

2.5 查询视图（减少开发重复join）
创建一个 view：把常用中日文一次性 join 出来：
CREATE OR REPLACE VIEW v_vehicle_i18n AS
SELECT
  v.*,
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
LEFT JOIN md_enum el ON el.enum_type='engine_layout' AND el.enum_code=v.engine_layout_code AND el.is_active=1
LEFT JOIN md_enum ft ON ft.enum_type='fuel_type' AND ft.enum_code=v.fuel_type_code AND ft.is_active=1
LEFT JOIN md_enum dt ON dt.enum_type='drive_type' AND dt.enum_code=v.drive_type_code AND dt.is_active=1;

应用层直接 SELECT * FROM v_vehicle_i18n，无需到处写 join。


## 3. vehicle_status
### Purpose
可变状态，允许被多个业务模块更新（但必须通过统一接口 & 记录日志）。

### Key Constraints
- UNIQUE(vehicle_id)

### Fields
- id (PK)
- vehicle_id (FK -> vehicle.id)
- status (available/rented/maintenance/reserved/inactive)
- mileage, fuel_level, speed, engine_on, alcohol_check_passed
- location_lat/lng, location_desc
- update_source (manual/rental/maintenance/gps/alcohol_check/system)
- update_time
- ext_json

## 4. vehicle_media
### Purpose
所有文件/附件归档（照片/保险/车检/酒测等）。

CREATE TABLE vehicle_media (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  vehicle_id INT NOT NULL,
  uploaded_by INT NOT NULL,

  file_type ENUM('photo','legal_doc') NOT NULL,
  file_path VARCHAR(255) NOT NULL,

  uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),

  KEY idx_vf_vehicle_id (vehicle_id),
  KEY idx_vf_vehicle_type (vehicle_id, file_type),
  KEY idx_vf_uploaded_by (uploaded_by),

  CONSTRAINT fk_vf_vehicle
    FOREIGN KEY (vehicle_id)
    REFERENCES vehicle(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_vf_uploaded_by
    FOREIGN KEY (uploaded_by)
    REFERENCES user(id)
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


## 5. vehicle_log
### Purpose
统一审计入口：扫码/编辑/状态更新/模块事件都写这里。

Fields:
- id (PK)
- vehicle_id (FK)
- actor (user/system)
- action_type
- action_detail (JSON)
- source_module
- created_at

## 6. vehicle_qr
### Purpose
二维码与车辆关联 + 访问 scope 定义（public/detail/edit/custom）。

Fields:
- id (PK)
- vehicle_id (FK)
- qr_slug (UNIQUE)
- qr_scope (public/detail/edit/custom)
- token_signature (optional)
- expired_at, is_active
- generated_by (FK -> user.id)
- generated_at, note

## 7. vehicle_field_permission
### Purpose
字段级可见/可编辑配置（前端必须通过宏调用此规则）。

vehicle_field_permission | CREATE TABLE `vehicle_field_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `table_name` varchar(64) NOT NULL,
  `field_name` varchar(64) NOT NULL,
  `access_level` int NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_role_table_field` (`role_id`,`table_name`,`field_name`),
  KEY `idx_role_id` (`role_id`),
  CONSTRAINT `fk_vfp_role` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=197 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 

vehicle_field_permission（字段级权限表）
一条记录代表：某角色（role_id）对某表某字段的访问级别


access_level 定义（INT）
10：VIEW（可见但只读）
20：EDIT（可编辑）

判定逻辑
可见：access_level >= 10
可编辑：access_level >= 20

UI 控制:
admin角色不需要配置，默认对所有用户所有表所有字段有可见和编辑权限。 无需也无法通过UI设置降低权限。
其他角色默认对业务表的所有表和所有字段都没有可见和编辑权限。 即无需通过UI设置为不可见。 UI上仅需要配置可见/可编辑。 如果配置为不可见，则代表删除这条记录，回到默认状态。

表格联动:
考虑到每次增加/删除/改动字段时，vehicle_field_permission也需要联动修改。
UI上设置字段权限时，table_name/field_name从 field_catalog表格读取，role name从role表获取。 均为下拉框选择。 table_name没有选中的时候，field_name为空。

CREATE TABLE IF NOT EXISTS field_catalog (
  id INT AUTO_INCREMENT PRIMARY KEY,
  table_name VARCHAR(64) NOT NULL,
  field_name VARCHAR(64) NOT NULL,
  data_type VARCHAR(64) NOT NULL,
  is_nullable TINYINT(1) NOT NULL,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_table_field (table_name, field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

每次启动UI去设置字段权限之前，用下面的命令刷新field_catalog表。
REPLACE INTO field_catalog (table_name, field_name, data_type, is_nullable)
SELECT table_name, column_name, data_type, (is_nullable='YES')
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name IN ('vehicle', 'vehicle_status', 'vehicle_qr', 'user', 'role');


## 8. RBAC Tables
- user: username/password_hash/role_id/is_active/is_deleted/expiored_time…
- role: role_code + bilingual name
- role_permission: (role_id, module_name, permission_type, allow_flag)
- 删除用户时，永远不在数据库中删除用户记录，而是把is_deleted置为1

## 9. Change Rules
- 不得把动态字段写入 vehicle（里程/油量/位置等）
- 任何新字段新增：优先 ext_json；高频稳定后再“升格”为列
- 所有跨模块状态更新必须写 vehicle_log


## 10.security
- 数据库服务器地址,端口,用户名,密码,读取 Vehicle_management\env.ini
  host
  port
  name
  user
  password
  charset

## 杂项
- 字段区分中日文时，必须以_cn 和 _jp结尾
