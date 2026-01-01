from ..repositories.field_permission_repo import list_field_permissions


class FieldPermissionService:
    """
    field_perm.can_view(table, field)
    field_perm.can_edit(table, field)
    """

    def __init__(self, current_user):
        self.user = current_user
        self.role = getattr(current_user, "role_code", "public") or "public"
        self.role_id = getattr(current_user, "role_id", None)
        self._rules = self._load_rules()
        self._system_fields = {
            "created_at",
            "created_by",
            "created_date",
            "updated_at",
            "updated_by",
            "updated_date",
        }

    def _load_rules(self):
        try:
            if not self.role_id:
                return {}
            rows = list_field_permissions(self.role_id)
        except Exception:
            rows = []
        return {
            (row["table_name"], row["field_name"]): row
            for row in rows
        }

    def get_access_level(self, table: str, field: str) -> int:
        if self.role == "admin":
            return 20
        if field in self._system_fields:
            return 0
        rule = self._rules.get((table, field))
        if not rule and field.endswith("_cn"):
            rule = self._rules.get((table, f"{field[:-3]}_jp"))
        if not rule and field.endswith("_jp"):
            rule = self._rules.get((table, f"{field[:-3]}_cn"))
        if not rule:
            return 0
        return int(rule.get("access_level") or 0)

    def can_view(self, table: str, field: str) -> bool:
        return self.get_access_level(table, field) >= 10

    def can_edit(self, table: str, field: str) -> bool:
        return self.get_access_level(table, field) >= 20
