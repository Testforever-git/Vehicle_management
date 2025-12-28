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
| Table   | Create Table                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| vehicle | CREATE TABLE `vehicle` (
  `id` int NOT NULL AUTO_INCREMENT,
  `brand_jp` varchar(64) DEFAULT NULL,
  `model_cn` varchar(64) DEFAULT NULL,
  `model_jp` varchar(64) DEFAULT NULL,
  `color_cn` varchar(32) DEFAULT NULL,
  `color_jp` varchar(32) DEFAULT NULL,
  `model_year` smallint unsigned DEFAULT NULL,
  `plate_no` varchar(64) DEFAULT NULL,
  `brand_cn` varchar(64) DEFAULT NULL,
  `vin` varchar(64) NOT NULL,
  `type_designation_code` varchar(64) DEFAULT NULL,
  `classification_number` varchar(32) DEFAULT NULL,
  `engine_code` varchar(32) DEFAULT NULL,
  `engine_layout` varchar(32) DEFAULT NULL,
  `displacement_cc` int unsigned DEFAULT NULL,
  `fuel_type` varchar(32) DEFAULT NULL,
  `drive_type` varchar(32) DEFAULT NULL,
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
  CONSTRAINT `fk_vehicle_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 


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

Fields:
- id (PK)
- table_name, field_name
- access_level (basic/advanced/admin)
- min_role_code
- is_visible, is_editable
- description
- UNIQUE(table_name, field_name)

## 8. RBAC Tables
- user: username/password_hash/role_id/is_active/…
- role: role_code + bilingual name
- role_permission: (role_id, module_name, permission_type, allow_flag)

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