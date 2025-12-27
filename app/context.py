# app/context.py
from flask import request, session, current_app, url_for
from .i18n import Translator
from .security.permissions import PermissionService
from .security.field_permissions import FieldPermissionService
from .security.mock_users import get_current_user

_translator = Translator()


def register_context(app):
    @app.context_processor
    def inject_globals():
        # 初始化默认值
        lang = current_app.config.get("APP_DEFAULT_LANG", "jp")
        current_user = None
        perms = None
        field_perm = None
        
        try:
            lang = request.args.get("lang") or session.get("lang") or current_app.config.get("APP_DEFAULT_LANG", "jp")
            session["lang"] = lang

            current_user = get_current_user()
            perms = PermissionService(current_user=current_user)
            field_perm = FieldPermissionService(current_user=current_user)
        except Exception as e:
            app.logger.error(f"Error in context processor: {e}")
            # Fallback to dummy objects
            class _Dummy:
                def can(self, *a, **k): return False
                def can_view(self, *a, **k): return False
                def can_edit(self, *a, **k): return False

            def _t(key: str) -> str:
                return key

            current_user = type("U", (), {"is_authenticated": False, "username": "guest", "role_code": "public", "full_name": ""})()
            perms = _Dummy()
            field_perm = _Dummy()
            lang = request.args.get("lang") or current_app.config.get("APP_DEFAULT_LANG", "jp")

        def t(key: str) -> str:
            # 使用安全的翻译函数，避免在异常处理中重复定义
            try:
                return _translator.t(lang, key)
            except:
                return key

        # ---- Safe language switch URLs (no **kwargs expansion in Jinja) ----
        try:
            endpoint = request.endpoint or "ui.dashboard"
            view_args = request.view_args or {}

            # request.args is ImmutableMultiDict -> convert to normal dict (keep last value)
            args_dict = dict(request.args)
            # don't keep old lang in query
            args_dict.pop("lang", None)

            def _lang_url(target_lang: str) -> str:
                # If endpoint needs params (like vehicle_id) they are in view_args
                return url_for(endpoint, **view_args, **args_dict, lang=target_lang)

            lang_url_jp = _lang_url("jp")
            lang_url_cn = _lang_url("cn")
        except:
            # 如果 URL 生成失败，提供默认值
            lang_url_jp = f"/?lang=jp"
            lang_url_cn = f"/?lang=cn"

        return {
            "lang": lang,
            "t": t,
            "perms": perms,
            "field_perm": field_perm,
            "current_user": current_user,
            "lang_url_jp": lang_url_jp,
            "lang_url_cn": lang_url_cn,
        }
