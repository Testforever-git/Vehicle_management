import json
from typing import Any, Optional

from app.db.mysql import execute


def log_vehicle_action(
    vehicle_id: Optional[int],
    actor: str,
    action_type: str,
    action_detail: Optional[dict[str, Any]],
    source_module: str,
):
    detail = json.dumps(action_detail or {}, ensure_ascii=False)
    try:
        execute(
            """
            INSERT INTO vehicle_log (vehicle_id, actor, action_type, action_detail, source_module, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (vehicle_id, actor, action_type, detail, source_module),
        )
    except Exception:
        return
