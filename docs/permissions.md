# Vehicle System — Permissions (V7)

> 单一真相：本文档定义权限模型（RBAC + 字段级权限 + QR scope）。  
> 前端与后端实现必须遵守。

## 0. Permission Layers
1) 功能权限（RBAC）：role_permission
2) 字段权限（Field-level）：vehicle_field_permission
3) QR 访问层级：vehicle_qr.qr_scope -> access_level

## 1. Roles
- viewer: 只读
- sales: 销售
- engineer: 整备/工程
- finance: 财务
- admin: 管理员
- customer: 客户

## 2. Module Permissions (role_permission)
permission_type:
- view / edit / delete / approve / export

Examples:
- vehicle:view  (viewer+)
- vehicle:edit  (sales/engineer/admin)
- vehicle:export (finance/admin)
- admin:*       (admin only)

## 3. Field Permissions (vehicle_field_permission)
Fields are governed by:
- access_level: basic / advanced / admin
- min_role_code: viewer / sales / engineer / finance / admin
- is_visible / is_editable

Rules:
- If not visible -> never render (UI + API)
- If visible but not editable -> render read-only (UI)
- Editable requires BOTH:
  - RBAC allow module:edit
  - field_permission.is_editable = true

## 4. QR Scopes
Mapping:
- qr_scope=public -> access_level=basic
- qr_scope=detail -> access_level=advanced (token or authorized login)
- qr_scope=edit   -> access_level=admin (login required)

QR behavior:
- Always log scan in vehicle_log(action_type='qr_view_*')
- Token (detail) should be short-lived (5-15 min)
- public never exposes sensitive fields (documents, full address, etc.)

## 5. Implementation Contract
Front-end:
- 禁止直接输出字段控件（input/dd/button）
- 必须使用统一宏:
  - display_field(table, field, ...)
  - input_field(table, field, ...)
  - action_button(module, action, ...)

Back-end:
- 提供两个统一判断函数/对象：
  - perms.can(module, action)
  - field_perm.can_view(table, field), field_perm.can_edit(table, field)
