# Vehicle System — UI Guidelines (V7)

> 单一真相：本文档定义 UI 页面与组件规范。  
> 保证风格统一 + 权限控制不遗漏。

## 0. Layout
- base.html: TopBar + SideNav + Content + Footer
- SideNav items controlled by RBAC (role_permission)

## 1. Pages
Core pages:
- /dashboard
- /vehicle/list
- /vehicle/<id>
- /vehicle/<id>/edit
- /vehicle/<id>/files
- /vehicle/<id>/logs
- /admin/users (admin)
- /admin/field_permissions (admin)
- /v/<qr_slug> (public)
- /v/<qr_slug>/detail (detail)

## 2. Mandatory UI Component Policy
All controls must pass through macros:
- display_field()  (view mode)
- input_field()    (edit mode; auto falls back to read-only if no edit permission)
- action_button()  (buttons; hidden if no permission)

## 3. Text Hierarchy (CSS tokens)
Define these classes and use consistently:
- .ac-title-main   : 页面主标题
- .ac-title-sub    : 卡片/区块标题
- .ac-field-label  : 字段名/label
- .ac-text-body    : 正文
- .ac-text-meta    : 辅助说明/时间/提示

## 4. Form & Display Style
- inputs: class "ac-input" (统一圆角、focus、间距)
- read-only display: class "ac-field-readonly"
- status badge: class "ac-badge-status"

## 5. Responsive Rules
- Desktop: detail page 30/70 columns
- Mobile: single column; filters collapse
- Tables: hide non-critical columns on <768px

## 6. QR Pages
- public page: minimal + safe fields only
- detail page: shows advanced status fields
- edit scope: redirects to login then to edit page (admin)

## 7. Language and Text Policy (Updated)
- 所有页面支持中日双语。统一使用navibar上的语言切换按钮进行切换
- 所有静态文本用yaml文件保存，每一个页面对一个一个yaml，每个yaml中用 cn/jp层级 区分不同语言的文本
- 保存在DB中的文本保存为中文，显示到页面时，如果切换了日文，则调用外部API进行翻译。 目前不实现，保留判断逻辑和API接口
