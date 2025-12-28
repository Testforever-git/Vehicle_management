class PermissionService:
    """
    perms.can(module, action)
    Later: replace this with role_permission table lookup.
    """
    def __init__(self, current_user):
        self.user = current_user
        self.matrix = {
            "public": {("vehicle", "view")},  # QR public uses basic view
            "viewer": {("dashboard", "view")},
            "sales": {("dashboard", "view"), ("vehicle", "view"), ("vehicle", "edit"), ("vehicle_qr", "view")},
            "engineer": {("dashboard", "view"), ("vehicle", "view"), ("vehicle", "edit"), ("status", "view"), ("vehicle_qr", "view")},
            "finance": {("dashboard", "view"), ("vehicle", "view"), ("vehicle", "export")},
            "admin": {("dashboard", "view"), ("vehicle", "view"), ("vehicle", "edit"), ("vehicle", "export"),
                      ("status", "view"), ("vehicle_qr", "view"),
                      ("admin", "view"), ("admin", "edit")},
        }

    def can(self, module: str, action: str) -> bool:
        role = getattr(self.user, "role_code", "public") or "public"
        if role == "admin":
            return True
        return (module, action) in self.matrix.get(role, set())
