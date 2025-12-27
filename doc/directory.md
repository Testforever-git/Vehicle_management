Vehicle_management/
├─ env.ini
├─ .env.example
├─ .gitignore
├─ README.md
│
├─ db/
│  └─ image/
│     └─ .gitkeep
│
└─ app/
   ├─ __init__.py
   ├─ wsgi.py
   ├─ config.py
   ├─ context.py
   ├─ i18n.py
   │
   ├─ data/
   │  └─ demo_data.py
   │
   ├─ security/
   │  ├─ mock_users.py
   │  ├─ permissions.py
   │  └─ field_permissions.py
   │
   ├─ utils/
   │  └─ masking.py
   │
   ├─ blueprints/
   │  ├─ auth/
   │  │  ├─ __init__.py
   │  │  └─ routes.py
   │  ├─ ui/
   │  │  ├─ __init__.py
   │  │  └─ routes.py
   │  ├─ qr/
   │  │  ├─ __init__.py
   │  │  └─ routes.py
   │  └─ admin/
   │     ├─ __init__.py
   │     └─ routes.py
   │
   ├─ templates/
   │  ├─ base.html
   │  ├─ dashboard.html
   │  ├─ auth/
   │  │  └─ login.html
   │  ├─ components/
   │  │  ├─ nav.html
   │  │  └─ footer.html
   │  ├─ macros/
   │  │  ├─ permissions.html
   │  │  ├─ controls.html
   │  │  └─ buttons.html
   │  ├─ vehicle/
   │  │  ├─ list.html
   │  │  ├─ detail.html
   │  │  └─ edit.html
   │  ├─ admin/
   │  │  ├─ users.html
   │  │  └─ field_permissions.html
   │  └─ qr/
   │     └─ public.html
   │
   └─ static/
      ├─ css/
      │  └─ ac-theme.css
      └─ i18n/
         ├─ jp.yaml
         └─ cn.yaml
