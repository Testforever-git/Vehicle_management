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
- UNIQUE(plate_no)

### Fields (summary)
- id (PK)
- vin, plate_no
- brand_cn/brand_jp, model_cn/model_jp, color_cn/color_jp, model_year
- type_designation_code（型式指定番号）, classification_number（類別区分番号）
- engine_code, engine_layout, displacement_cc, fuel_type, drive_type, transmission
- ownership_type, owner_id, driver_id
- garage_name, garage_address_jp/cn, garage_postcode, garage_lat/lng
- purchase_date, purchase_price
- legal_doc, vehicle_photo
- ext_json, note, created_at, updated_at

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

Fields:
- id (PK)
- vehicle_id (FK)
- file_type, file_path, description, uploaded_by, uploaded_at

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
