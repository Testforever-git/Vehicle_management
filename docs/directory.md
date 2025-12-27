目录架构:

Vehicle_management/
├─ README.md
├─ pyproject.toml                 # 或 requirements.txt
├─ .env.example                   # 环境变量模板（不提交 .env）
├─ .gitignore
│
├─ docs/
│  ├─ vehicle/
│  │  ├─ db_schema.md
│  │  ├─ permissions.md
│  │  └─ ui_guidelines.md
│  │  └─ directory.md
│  ├─ api/
│  │  ├─ vehicle_api.md           # 可选：车辆 API 说明
│  │  └─ auth_api.md              # 可选：认证与权限说明
│  └─ adr/                        # Architecture Decision Records（建议）
│     ├─ 0001-vehicle-v7-schema.md
│     └─ 0002-field-permission-macros.md
│
├─ migrations/                    # Alembic（推荐）或 Flask-Migrate
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
│
├─ db/
│  ├─ schema/
│  │  ├─ V7_ddl.sql               # 定版 DDL（只读基准，变更走 migration）
│  │  └─ seed/
│  │     ├─ 00_roles.sql          # role 初始数据
│  │     ├─ 01_role_permissions.sql
│  │     └─ 02_vehicle_field_permissions.sql
│  └─ notes/
│     ├─ naming_conventions.md
│     └─ indexes_and_constraints.md
│
├─ app/
│  ├─ __init__.py                 # create_app(), 注册蓝图、扩展、context_processor
│  ├─ config.py                   # Config 类（DEV/PROD）
│  ├─ extensions.py               # db/login_manager/bcrypt/csrf等
│  ├─ context.py                  # 注入 t(), perms, field_perm, lang
│  ├─ security/
│  │  ├─ permissions.py           # perms.can(module, action) 实现
│  │  ├─ field_permissions.py     # field_perm.can_view/can_edit 实现
│  │  ├─ tokens.py                # QR detail token（短期签名）
│  │  └─ audit.py                 # vehicle_log 写入工具
│  │
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ user.py                  # user/role/role_permission
│  │  ├─ vehicle.py               # vehicle/vehicle_status/vehicle_media/vehicle_log
│  │  ├─ qr.py                    # vehicle_qr
│  │  └─ field_permission.py      # vehicle_field_permission
│  │
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ vehicle_service.py       # 车辆查询/更新（统一入口）
│  │  ├─ status_service.py        # 状态更新入口（写log）
│  │  ├─ qr_service.py            # 生成/失效二维码
│  │  └─ admin_service.py         # 用户/权限配置
│  │
│  ├─ blueprints/
│  │  ├─ auth/
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py             # /login /logout
│  │  │  └─ forms.py
│  │  │
│  │  ├─ ui/
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py             # /dashboard /vehicle/... /status/...
│  │  │  ├─ forms.py              # VehicleForm（可选）
│  │  │  └─ view_models.py        # 模板用 view model（mask_plate等）
│  │  │
│  │  ├─ qr/
│  │  │  ├─ __init__.py
│  │  │  └─ routes.py             # /v/<slug> /v/<slug>/detail
│  │  │
│  │  └─ admin/
│  │     ├─ __init__.py
│  │     ├─ routes.py             # /admin/users /admin/field_permissions
│  │     └─ forms.py
│  │
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ components/
│  │  │  ├─ nav.html              # 你的旧版可直接放这里复用
│  │  │  ├─ footer.html
│  │  │  ├─ flash.html
│  │  │  └─ pagination.html
│  │  ├─ macros/
│  │  │  ├─ permissions.html      # can()/can_view_field()/can_edit_field()
│  │  │  ├─ controls.html         # display_field()/input_field()
│  │  │  └─ buttons.html          # action_button()
│  │  ├─ vehicle/
│  │  │  ├─ list.html
│  │  │  ├─ detail.html
│  │  │  ├─ edit.html
│  │  │  ├─ files.html
│  │  │  └─ logs.html
│  │  ├─ status/
│  │  │  └─ overview.html
│  │  ├─ admin/
│  │  │  ├─ users.html
│  │  │  └─ field_permissions.html
│  │  └─ qr/
│  │     ├─ public.html
│  │     └─ detail.html
│  │
│  ├─ static/
│  │  ├─ css/
│  │  │  ├─ bootstrap.min.css     # 或用 CDN（推荐自己管理版本）
│  │  │  ├─ ac-theme.css          # 统一 UI 风格（你要的：主标题/副标题/正文等）
│  │  │  └─ app.css               # 少量页面级覆写（可选）
│  │  ├─ js/
│  │  │  ├─ bootstrap.bundle.min.js
│  │  │  └─ app.js                # 自己的脚本（可选）
│  │  ├─ img/
│  │  │  └─ logo.svg
│  │  └─ i18n/
│  │     ├─ jp.yaml               # 日文文案
│  │     └─ cn.yaml               # 中文文案
│  │
│  ├─ utils/
│  │  ├─ slug.py                  # qr_slug 生成/解析（hashids/uuid-base62）
│  │  ├─ masking.py               # mask_plate / 脱敏工具
│  │  ├─ datetime.py              # timezone helpers (Asia/Tokyo)
│  │  └─ validators.py            # VIN/型式等校验
│  │
│  └─ wsgi.py                      # gunicorn entry
│
├─ tests/
│  ├─ test_auth.py
│  ├─ test_vehicle_permissions.py  # 权限与字段过滤必须测
│  ├─ test_qr_scope.py
│  └─ test_vehicle_pages.py
│
└─ scripts/
   ├─ init_db.sh                   # 初始化迁移/seed（可选）
   └─ seed_dev.py                  # 开发环境快速造数据
