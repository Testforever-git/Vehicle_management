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
  `etc_type` enum('none','etc1','etc2') NOT NULL DEFAULT 'none' COMMENT 'ETC设备类型: none=无, etc1=ETC1.0, etc2=ETC2.0',
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
  CONSTRAINT `fk_vehicle_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

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
通过app\static\i18n\convert_year.yaml来转换。

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
vehicle_status | CREATE TABLE `vehicle_status` (
  `vehicle_id` int NOT NULL,
  `status` varchar(32) DEFAULT NULL COMMENT 'available/rented/maintenance/reserved/inactive',
  `mileage` int DEFAULT NULL,
  `fuel_level` int DEFAULT NULL COMMENT '0-100',
  `location_desc` varchar(255) DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `updated_by` int DEFAULT NULL COMMENT '最后更新该状态的用户ID',
  `inspection_due_yyyymm` int unsigned DEFAULT NULL COMMENT '車検満了年月 (YYYYMM, e.g. 202602)',
  `insurance_due_date` date DEFAULT NULL COMMENT '任意保険満了日 (YYYY-MM-DD)',
  `has_etc_card` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已插入ETC卡 (1=有卡，可直接使用ETC)',
  PRIMARY KEY (`vehicle_id`),
  KEY `idx_vehicle_status_updated_by` (`updated_by`),
  KEY `idx_inspection_due_yyyymm` (`inspection_due_yyyymm`),
  KEY `idx_insurance_due_date` (`insurance_due_date`),
  CONSTRAINT `fk_vehicle_status_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_vehicle_status_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicle` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

status信息可以被人工修改，也可以被外部设备修改。（比如GPS或者其他设备)

## 4. vehicle_media
### Purpose
所有文件/附件归档（照片/保险/车检/酒测等）。

CREATE TABLE vehicle_media (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  vehicle_id INT NOT NULL,
  uploaded_by INT NOT NULL,
  
  file_type ENUM('photo','legal_doc') NOT NULL,
  file_path VARCHAR(255) NOT NULL,
  is_primary tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为车辆代表图(封面图)',
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


## 5. audit_log
### Purpose
统一审计入口： 记录系统数据的变化以及用户的登入登出。

CREATE TABLE IF NOT EXISTS `audit_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `vehicle_id` INT NULL COMMENT '可为空；与 vehicle.id 关联（如登录/登出时为空）',
  `actor` ENUM('user','system') NOT NULL DEFAULT 'system' COMMENT '操作主体：用户/系统',
  `actor_id` INT NULL COMMENT 'actor=user 时应为 user.id；actor=system 时为空',
  `action_type` ENUM('login','logout','insert','delete','update') NOT NULL,
  `action_detail` JSON NOT NULL COMMENT '结构化审计信息（table/pk/fields/message 等）',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  KEY `idx_audit_created_at` (`created_at`),
  KEY `idx_audit_vehicle_id` (`vehicle_id`),
  KEY `idx_audit_actor` (`actor`,`actor_id`),
  KEY `idx_audit_action_type` (`action_type`,`created_at`),
  CONSTRAINT `fk_audit_vehicle`
    FOREIGN KEY (`vehicle_id`) REFERENCES `vehicle`(`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT `fk_audit_actor_user`
    FOREIGN KEY (`actor_id`) REFERENCES `user`(`id`)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
  CONSTRAINT `chk_audit_action_detail_json`
    CHECK (JSON_VALID(`action_detail`))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

action_detail sample1:
{
  "table": "vehicle",
  "pk": {"id": 123},
  "op": "update",
  "fields": {
    "purchase_price": {"old": 1000000, "new": 1100000}
  },
  "message": "在vehicle表修改purchase_price字段"
}
action_detail sample2:
{
  "op": "login",
  "context": {
    "ip": "1.2.3.4",
    "user_agent": "Chrome/143.0",
    "session_id": "sess_xxx"
  },
  "message": "登录"
}
UI上显示 用户 + action_detail.message

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
is_audited 字段决定table_name，field_name是否被 audit_log审计。

CREATE TABLE `field_catalog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `table_name` varchar(64) NOT NULL,
  `field_name` varchar(64) NOT NULL,
  `data_type` varchar(64) NOT NULL,
  `is_nullable` tinyint(1) NOT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_audited` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否参与审计：字段级 / 表级(__TABLE__)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_table_field` (`table_name`,`field_name`)
) ENGINE=InnoDB AUTO_INCREMENT=9458 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 

每次启动UI去设置字段权限之前，用下面的命令刷新field_catalog表。
REPLACE INTO field_catalog (table_name, field_name, data_type, is_nullable)
SELECT table_name, column_name, data_type, (is_nullable='YES')
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name IN ('vehicle', 'vehicle_status', 'vehicle_qr', 'user', 'role');


- user: username/password_hash/role_id/is_active/is_deleted/expiored_time…
- role: role_code + bilingual name
- role_permission: (role_id, module_name, permission_type, allow_flag)
- 删除用户时，永远不在数据库中删除用户记录，而是把is_deleted置为1


- 任何新字段新增：优先 ext_json；高频稳定后再“升格”为列
- 所有跨模块状态更新必须写 audit_log




## 11.customer 客户管理
- 用户管理表
customer（客户主档）
用途：客户“是谁”，以及少量展示字段。不存验证码、不存积分流水、不存复杂权益。

CREATE TABLE customer (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_no VARCHAR(32) NOT NULL COMMENT '客户编号(业务展示用，可用规则生成)',
  customer_type ENUM('personal','company') NOT NULL DEFAULT 'personal',

  display_name VARCHAR(128) DEFAULT NULL,
  full_name VARCHAR(128) DEFAULT NULL,
  full_name_kana VARCHAR(128) DEFAULT NULL,

  -- 个人车主为主：可选信息
  birthday DATE DEFAULT NULL,
  gender ENUM('unknown','male','female','other') NOT NULL DEFAULT 'unknown',

  -- 合规与运营
  status ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active',
  last_login_at DATETIME DEFAULT NULL,

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_customer_no (customer_no),
  KEY idx_customer_type (customer_type),
  KEY idx_customer_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


- customer_auth_identity（登录身份表）
用途：让一个客户可以有多个登录方式（email/phone），并支持未来三方登录。
主流做法：email/phone 不直接塞 customer 表，而是 identity 表管理，并标记 primary。

CREATE TABLE customer_auth_identity (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,

  identity_type ENUM('email','phone','oauth') NOT NULL,
  identifier VARCHAR(255) NOT NULL COMMENT '邮箱/手机号/三方openid等',

  is_primary TINYINT(1) NOT NULL DEFAULT 0,
  verified_at DATETIME DEFAULT NULL,

  -- 用于 oauth 扩展
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

运营建议：
同一个 customer_id 最多一个 is_primary=1（可在应用层保证；如需数据库强约束可用 generated column + unique trick，后面再加）

- customer_verification_code（验证码）

用途：注册/登录/找回/换绑的验证码，支持短信和邮件。 
注: 目前无法实现发送sms和邮件进行认证的功能，仅保留接口

CREATE TABLE customer_verification_code (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  target VARCHAR(255) NOT NULL COMMENT '手机号或邮箱(与identity.identifier一致)',
  channel ENUM('sms','email') NOT NULL,
  purpose ENUM('register','login','reset','change_contact') NOT NULL,

  code VARCHAR(16) NOT NULL,
  expired_at DATETIME NOT NULL,
  used_at DATETIME DEFAULT NULL,

  -- 风控与排障
  created_ip VARCHAR(64) DEFAULT NULL,
  user_agent VARCHAR(255) DEFAULT NULL,
  attempts INT NOT NULL DEFAULT 0 COMMENT '验证失败次数(可选)',
  sent_count INT NOT NULL DEFAULT 1 COMMENT '同一记录的发送次数(可选)',

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_target (target),
  KEY idx_target_purpose (target, purpose),
  KEY idx_expired (expired_at),
  KEY idx_channel_purpose (channel, purpose)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- member_tier（会员等级字典）
用途：会员分级与权益参数（先用 JSON 预留，后期可拆规则表）。
注: 目前无计划上线会员，仅保留接口
CREATE TABLE member_tier (
  code VARCHAR(32) NOT NULL,
  name_ja VARCHAR(64) NOT NULL,
  name_zh VARCHAR(64) NOT NULL,
  rank_no INT NOT NULL COMMENT '等级排序(数字越大等级越高)',
  is_active TINYINT(1) NOT NULL DEFAULT 1,

  -- 预留：升级条件、折扣、权益等
  upgrade_rule_json JSON DEFAULT NULL,
  benefit_json JSON DEFAULT NULL,

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (code),
  UNIQUE KEY uq_rank_no (rank_no),
  KEY idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- customer_membership（客户会员快照）
用途：记录“这个客户当前是什么会员”，以及积分余额/累计消费快照（可选）。
说明：积分余额可以放这里作为快照，但以流水为准。
注: 目前无计划上线会员，仅保留接口

CREATE TABLE customer_membership (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,

  tier_code VARCHAR(32) NOT NULL DEFAULT 'normal',
  member_since DATE DEFAULT NULL,
  member_until DATE DEFAULT NULL COMMENT '如有有效期会员可用',

  points_balance INT NOT NULL DEFAULT 0,
  lifetime_spend_yen BIGINT UNSIGNED NOT NULL DEFAULT 0,

  status ENUM('active','frozen','ended') NOT NULL DEFAULT 'active',

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_customer_membership (customer_id),
  KEY idx_tier (tier_code),
  KEY idx_status (status),

  CONSTRAINT fk_customer_membership_customer
    FOREIGN KEY (customer_id) REFERENCES customer(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,

  CONSTRAINT fk_customer_membership_tier
    FOREIGN KEY (tier_code) REFERENCES member_tier(code)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- customer_points_ledger（积分流水）
用途：对账、审计、退款回滚、人工调整。只存余额会必踩坑，主流系统一定有流水。
注: 目前无计划上线会员，仅保留接口
CREATE TABLE customer_points_ledger (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,

  direction ENUM('earn','spend','expire','adjust','refund') NOT NULL,
  points INT NOT NULL COMMENT '正数；direction 决定增减',
  balance_after INT DEFAULT NULL COMMENT '可选：写入变更后余额快照，便于审计',

  reason_code VARCHAR(32) DEFAULT NULL COMMENT '规则/原因编码(可选)',
  ref_type VARCHAR(32) DEFAULT NULL COMMENT '关联对象类型(如 repair_order/rental/...)',
  ref_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联对象ID(可选)',

  note VARCHAR(255) DEFAULT NULL,
  operator_user_id BIGINT UNSIGNED DEFAULT NULL COMMENT '内部操作人(user.id)，自动系统可为空',

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_customer_time (customer_id, created_at),
  KEY idx_ref (ref_type, ref_id),

  CONSTRAINT fk_points_ledger_customer
    FOREIGN KEY (customer_id) REFERENCES customer(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- communication_log（短信/邮件发送日志）

用途：排查“客户收不到验证码/通知”时的关键证据；也可用于统计成本。

CREATE TABLE communication_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  customer_id BIGINT UNSIGNED DEFAULT NULL,
  channel ENUM('sms','email') NOT NULL,
  purpose ENUM('verification','notice','marketing') NOT NULL,

  target VARCHAR(255) NOT NULL COMMENT '手机号或邮箱',
  template_code VARCHAR(64) DEFAULT NULL,
  content_preview VARCHAR(255) DEFAULT NULL COMMENT '内容摘要(避免存敏感完整内容)',
  provider VARCHAR(64) DEFAULT NULL COMMENT 'twilio/sns/ses/sendgrid等',
  provider_message_id VARCHAR(128) DEFAULT NULL,

  status ENUM('queued','sent','failed') NOT NULL DEFAULT 'queued',
  error_code VARCHAR(64) DEFAULT NULL,
  error_message VARCHAR(255) DEFAULT NULL,

  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at DATETIME DEFAULT NULL,

  PRIMARY KEY (id),
  KEY idx_customer_time (customer_id, created_at),
  KEY idx_target_time (target, created_at),
  KEY idx_status_time (status, created_at),

  CONSTRAINT fk_communication_log_customer
    FOREIGN KEY (customer_id) REFERENCES customer(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- 业务规则
identity 唯一性：同一邮箱/手机号只能绑定到一个 customer（uq_identity 保证）。
验证码有效期：5–10 分钟；用过必须写 used_at；验证失败次数/频率限制由应用层实现。
积分以流水为准：customer_membership.points_balance 允许做快照，但必须能从 customer_points_ledger 复算。
通知必须记录 log：验证码/重要通知必须写 communication_log，否则排障困难。
软删除：客户删号/合规删除优先 status='deleted'，历史订单/工单引用不应断。


## 12 租赁系统
- 订单主表 记录客户发起的订单。
  rental_booking | CREATE TABLE `rental_booking` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `booking_code` varchar(32) NOT NULL,
  `customer_id` bigint unsigned DEFAULT NULL,
  `vehicle_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `pickup_mode` enum('store','delivery') NOT NULL DEFAULT 'store',
  `pickup_store_id` int DEFAULT NULL,
  `pickup_address_jp` varchar(255) DEFAULT NULL,
  `pickup_postcode` varchar(16) DEFAULT NULL,
  `pickup_lat` decimal(10,7) DEFAULT NULL,
  `pickup_lng` decimal(10,7) DEFAULT NULL,
  `dropoff_mode` enum('store','pickup') NOT NULL DEFAULT 'store',
  `dropoff_store_id` int DEFAULT NULL,
  `dropoff_address_jp` varchar(255) DEFAULT NULL,
  `dropoff_postcode` varchar(16) DEFAULT NULL,
  `dropoff_lat` decimal(10,7) DEFAULT NULL,
  `dropoff_lng` decimal(10,7) DEFAULT NULL,
  `pickup_location` varchar(128) DEFAULT NULL,
  `return_location` varchar(128) DEFAULT NULL,
  `status` enum('pending_review','awaiting_docs','awaiting_payment','confirmed','picked_up','returned','closed','cancelled','no_show') NOT NULL DEFAULT 'pending_review',
  `currency` char(3) NOT NULL DEFAULT 'JPY',
  `price_snapshot` json NOT NULL,
  `payment_status` enum('unpaid','authorized','paid','partially_refunded','refunded','failed') NOT NULL DEFAULT 'unpaid',
  `deposit_status` enum('none','authorized','captured','released') NOT NULL DEFAULT 'none',
  `note` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by` int DEFAULT NULL,
  `access_token` varchar(64) NOT NULL,
  `access_token_expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rental_booking_code` (`booking_code`),
  UNIQUE KEY `uk_rental_booking_access_token` (`access_token`),
  KEY `idx_booking_vehicle_date` (`vehicle_id`,`start_date`,`end_date`),
  KEY `idx_booking_status` (`status`),
  KEY `idx_booking_customer` (`customer_id`),
  KEY `fk_booking_updated_by` (`updated_by`),
  CONSTRAINT `fk_booking_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_booking_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicle` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  
  rental_booking.price_snapshot sample:
    {
  "pricing_version": "v1",
  "days": 7,
  "base": {
    "daily_price": 12000,
    "base_rent": 84000
  },
  "longterm_discount": {
    "rule_id": 3,
    "type": "percent",
    "value": 90,
    "discounted_rent": 75600
  },
  "insurance": {
    "per_day": 800,
    "total": 5600
  },
  "deposit": 30000,
  "services": [
    {"service_id": 1, "name": "チャイルドシート", "pricing": "per_day", "unit_price": 500, "qty": 1, "total": 3500}
  ],
  "tax": {
    "rate": 10.0,
    "taxable": 79100,
    "amount": 7910
  },
  "total": 87010
}

  
- 客户证件表（按订单绑定）。支持驾照 + 身份证件/在留卡/护照，多份文件，且带审核状态。暂不实现。
- 订单短时锁，防止多人同时提交同车同日期。暂不实现。
- 运营屏蔽区间，用来表达“仅某几天不可租”（维修、内部用车、调车）。暂不实现。
- 交接记录。 取车还车。暂不实现。


- 定价表
  CREATE TABLE rental_vehicle_pricing (
  vehicle_id INT NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'JPY',

  daily_price INT NOT NULL,         -- 基础日价
  deposit_amount INT NOT NULL DEFAULT 0,
  insurance_per_day INT NOT NULL DEFAULT 0,

  free_km_per_day INT DEFAULT NULL,
  extra_km_price INT DEFAULT NULL,

  cleaning_fee INT NOT NULL DEFAULT 0,
  late_fee_per_day INT NOT NULL DEFAULT 0,  -- 按天（你按天最小单位）

  tax_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,

  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by INT DEFAULT NULL,

  PRIMARY KEY (vehicle_id),
  CONSTRAINT fk_pricing_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE,
  CONSTRAINT fk_pricing_updated_by FOREIGN KEY (updated_by) REFERENCES user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



- 折扣表
  CREATE TABLE rental_longterm_discount_rule (
  id INT NOT NULL AUTO_INCREMENT,
  vehicle_id INT NOT NULL,                       -- 先按车，未来你也可改成 group_id
  min_days INT NOT NULL,
  max_days INT DEFAULT NULL,                     -- NULL 表示无上限

  discount_type ENUM('percent','amount') NOT NULL,
  discount_value INT NOT NULL,                   -- percent 用 90 表示 90%（即9折）；amount 用日元

  priority INT NOT NULL DEFAULT 100,             -- 多规则命中时取 priority 最小
  is_active TINYINT(1) NOT NULL DEFAULT 1,

  valid_from DATE DEFAULT NULL,
  valid_to   DATE DEFAULT NULL,

  PRIMARY KEY (id),
  KEY idx_discount_vehicle_days (vehicle_id, min_days, max_days, is_active),
  CONSTRAINT fk_discount_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

按“租期天数区间”命中折扣规则，并支持两种折扣方式：
如： percent：9折、8折
     amount：每天减 1000 日元
长租优惠计算sample:
base_rent = daily_price * rental_days
查找命中规则：满足 min_days <= rental_days 且 (max_days IS NULL OR rental_days <= max_days) 且 active 且日期有效
取 priority 最小的一条
计算折扣：
percent：discounted_rent = base_rent * discount_value / 100
amount：discounted_rent = base_rent - (discount_value * rental_days)
rent_final = max(discounted_rent, 0)


- 额外服务定价表. 儿童座椅/雪胎/送车上门等等
  CREATE TABLE rental_service_catalog (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- 订单选择了哪些服务的关联表 暂不实现
  CREATE TABLE rental_booking_service (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  booking_id BIGINT UNSIGNED NOT NULL,
  service_id INT NOT NULL,
  qty INT NOT NULL DEFAULT 1,
  price_snapshot JSON NOT NULL,  -- 本单该服务的计价结果（例如 per_day * 天数）
  PRIMARY KEY (id),
  KEY idx_booking_service_booking (booking_id),
  CONSTRAINT fk_booking_service_booking FOREIGN KEY (booking_id) REFERENCES rental_booking(id) ON DELETE CASCADE,
  CONSTRAINT fk_booking_service_service FOREIGN KEY (service_id) REFERENCES rental_service_catalog(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

- 租车需求（业务流程验证）
  CREATE TABLE rental_request (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT NOT NULL,
  customer_id BIGINT UNSIGNED NOT NULL,

  start_date DATE NOT NULL,
  end_date DATE NOT NULL,

  delivery_lat DECIMAL(10,7) DEFAULT NULL,
  delivery_lng DECIMAL(10,7) DEFAULT NULL,
  delivery_address VARCHAR(255) DEFAULT NULL,

  service_ids JSON DEFAULT NULL,
  note TEXT,

  status ENUM('new','reviewed','cancelled') NOT NULL DEFAULT 'new',

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_rental_request_vehicle (vehicle_id),
  KEY idx_rental_request_customer (customer_id),
  KEY idx_rental_request_status (status),
  CONSTRAINT fk_rental_request_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicle(id) ON DELETE CASCADE,
  CONSTRAINT fk_rental_request_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

推荐状态流：

客户创建订单 → pending_review
客户上传证件 → 后台审核证件
证件不全：awaiting_docs
审核通过 → awaiting_payment（生成 hold）
支付成功 → confirmed（库存占用生效）
取车交接 → picked_up（同时写 rental_handover(pickup)，更新 vehicle_status 读数）
还车交接 → returned（写 rental_handover(return)）
结算（生成/追加 charges，退款/补扣完成）→ closed

取消：
支付前：cancelled（释放 hold）
支付后：cancelled + 退款（支付系统阶段实现）

## 13.汽车修理/保养系统
留白


## 99.security
- 数据库服务器地址,端口,用户名,密码,读取 Vehicle_management\env.ini
  host
  port
  name
  user
  password
  charset

## 100.其他相关表格。
- brand字典
  md_brand | CREATE TABLE `md_brand` (
  `id` int NOT NULL AUTO_INCREMENT,
  `brand_code` varchar(32) NOT NULL,
  `name_jp` varchar(64) NOT NULL,
  `name_cn` varchar(64) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int NOT NULL DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_brand_code` (`brand_code`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

- model字典
  md_model | CREATE TABLE `md_model` (
  `id` int NOT NULL AUTO_INCREMENT,
  `brand_id` int NOT NULL,
  `model_code` varchar(64) NOT NULL,
  `name_jp` varchar(64) NOT NULL,
  `name_cn` varchar(64) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int NOT NULL DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_brand_model_code` (`brand_id`,`model_code`),
  KEY `idx_model_brand` (`brand_id`,`is_active`,`sort_order`),
  CONSTRAINT `fk_model_brand` FOREIGN KEY (`brand_id`) REFERENCES `md_brand` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

- 颜色字典
  md_color | CREATE TABLE `md_color` (
  `id` int NOT NULL AUTO_INCREMENT,
  `color_code` varchar(32) NOT NULL,
  `name_jp` varchar(32) NOT NULL,
  `name_cn` varchar(32) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int NOT NULL DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_color_code` (`color_code`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

- FF/FW/RWD等字典
  md_enum | CREATE TABLE `md_enum` (
  `id` int NOT NULL AUTO_INCREMENT,
  `enum_type` varchar(32) NOT NULL,
  `enum_code` varchar(32) NOT NULL,
  `name_jp` varchar(64) NOT NULL,
  `name_cn` varchar(64) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int NOT NULL DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_enum` (`enum_type`,`enum_code`),
  KEY `idx_enum_type` (`enum_type`,`is_active`,`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
