# app/__init__.py
from flask import Flask

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---- IMPORTANT: set SECRET_KEY so session works ----
    app.config["SECRET_KEY"] = "dev-secret-key-change-me"
    app.config.setdefault("APP_DEFAULT_LANG", "jp")

    # ---- Register context processor (lang/t/perms/field_perm/current_user) ----
    try:
        from .db.schema import ensure_schema
        ensure_schema()
        app.logger.info("Database schema ensured.")
    except Exception as e:
        app.logger.exception("Failed to ensure database schema: %s", e)

    try:
        from .context import register_context
        register_context(app)
        app.logger.info("Context processor registered.")
    except Exception as e:
        # If context registration fails, app can still boot; template won't crash
        app.logger.exception("Failed to register context processor: %s", e)

        @app.context_processor
        def _fallback_context():
            class _Dummy:
                def can(self, *a, **k): return False
                def can_view(self, *a, **k): return False
                def can_edit(self, *a, **k): return False

            def _t(key: str) -> str:
                return key

            return {
                "lang": "jp",
                "t": _t,
                "perms": _Dummy(),
                "field_perm": _Dummy(),
                "current_user": type("U", (), {"is_authenticated": False, "username": "guest", "role_code": "public", "full_name": ""})(),
                "lang_url_jp": "/?lang=jp",
                "lang_url_cn": "/?lang=cn",
            }

    # ---- Blueprints ----
    from .blueprints.auth import bp as auth_bp
    from .blueprints.ui import bp as ui_bp
    from .blueprints.qr import bp as qr_bp
    from .blueprints.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(admin_bp)

    return app
