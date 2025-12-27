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
        lang = request.args.get("lang") or session.get("lang") or current_app.config.get("APP_DEFAULT_LANG", "jp")
        session["lang"] = lang

        current_user = get_current_user()
        perms = PermissionService(current_user=current_user)
        field_perm = FieldPermissionService(current_user=current_user)

        def t(key: str) -> str:
            return _translator.t(lang, key)

        # ---- Safe language switch URLs (no **kwargs expansion in Jinja) ----
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

        return {
            "lang": lang,
            "t": t,
            "perms": perms,
            "field_perm": field_perm,
            "current_user": current_user,
            "lang_url_jp": lang_url_jp,
            "lang_url_cn": lang_url_cn,
        }
