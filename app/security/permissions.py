from ..repositories.permission_repo import list_role_permissions


class PermissionService:
    """
    perms.can(module, action)
    Uses role_permission table for RBAC.
    """

    def __init__(self, current_user):
        self.user = current_user
        self.role = getattr(self.user, "role_code", "public") or "public"
        self._permissions = self._load_permissions()

    def _load_permissions(self):
        if self.role == "public":
            return {("vehicle", "view")}
        try:
            rows = list_role_permissions(self.role)
            return {(row["module_name"], row["permission_type"]) for row in rows if row.get("allow_flag")}
        except Exception:
            return set()

    def can(self, module: str, action: str) -> bool:
        if self.role == "admin":
            return True
        return (module, action) in self._permissions
