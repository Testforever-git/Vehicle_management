from ..repositories.field_permission_repo import list_field_permissions


class FieldPermissionService:
    """
    field_perm.can_view(table, field)
    field_perm.can_edit(table, field)
    """

    def __init__(self, current_user):
        self.user = current_user
        self.role = getattr(current_user, "role_code", "public") or "public"
        self._rules = self._load_rules()

    def _load_rules(self):
        try:
            rows = list_field_permissions()
        except Exception:
            rows = []
        return {
            (row["table_name"], row["field_name"]): row
            for row in rows
        }

    def _role_rank(self, role_code: str) -> int:
        rank = {
            "public": 1,
            "user": 1,
            "engineer": 2,
            "admin": 3,
        }
        return rank.get(role_code, 0)

    def _level_rank(self, level: str) -> int:
        return {"basic": 1, "advanced": 2, "admin": 3}.get(level, 3)

    def _can_access(self, rule: dict) -> bool:
        access_rank = self._level_rank(rule.get("access_level", "admin"))
        min_role_rank = self._role_rank(rule.get("min_role_code", "admin"))
        required_rank = max(access_rank, min_role_rank)
        return self._role_rank(self.role) >= required_rank

    def can_view(self, table: str, field: str) -> bool:
        rule = self._rules.get((table, field))
        if not rule:
            return self.role == "admin"
        if not rule.get("is_visible"):
            return False
        return self._can_access(rule)

    def can_edit(self, table: str, field: str) -> bool:
        rule = self._rules.get((table, field))
        if not rule:
            return self.role == "admin"
        if not rule.get("is_editable"):
            return False
        return self._can_access(rule)
