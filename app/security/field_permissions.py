class FieldPermissionService:
    """
    field_perm.can_view(table, field)
    field_perm.can_edit(table, field)

    Later: replace rules with vehicle_field_permission table lookup.
    """
    def __init__(self, current_user):
        self.user = current_user
        self.role = getattr(current_user, "role_code", "public") or "public"

        # table.field -> (access_level, editable)
        self.rules = {
            ("vehicle", "brand_jp"): ("basic", False),
            ("vehicle", "model_jp"): ("basic", False),
            ("vehicle", "plate_no"): ("basic", False),

            ("vehicle", "vin"): ("advanced", False),
            ("vehicle", "type_designation_code"): ("advanced", False),

            ("vehicle", "garage_name"): ("advanced", True),
            ("vehicle", "garage_address_jp"): ("advanced", True),

            ("vehicle", "purchase_price"): ("admin", True),

            # NEW (C): dirs should be visible to advanced+, editable by admin only (you can change later)
            ("vehicle", "legal_doc_dir"): ("advanced", False),
            ("vehicle", "vehicle_photo_dir"): ("advanced", False),

            ("vehicle_status", "status"): ("basic", False),
            ("vehicle_status", "mileage"): ("advanced", False),
            ("vehicle_status", "fuel_level"): ("advanced", False),
            ("vehicle_status", "location_desc"): ("advanced", False),
        }

    def _level_ok(self, level: str) -> bool:
        if level == "basic":
            return self.role in ["public", "viewer", "sales", "engineer", "finance", "admin"]
        if level == "advanced":
            return self.role in ["sales", "engineer", "finance", "admin"]
        if level == "admin":
            return self.role == "admin"
        return False

    def can_view(self, table: str, field: str) -> bool:
        level, _editable = self.rules.get((table, field), ("admin", False))
        return self._level_ok(level)

    def can_edit(self, table: str, field: str) -> bool:
        level, editable = self.rules.get((table, field), ("admin", False))
        return editable and self._level_ok(level)
