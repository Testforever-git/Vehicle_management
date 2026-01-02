import json
from typing import Any, Optional

from ..db.mysql import execute, fetch_all, fetch_one


def create_audit_log(
    vehicle_id: Optional[int],
    actor: str,
    actor_id: Optional[int],
    action_type: str,
    action_detail: dict[str, Any],
):
    detail = json.dumps(action_detail, ensure_ascii=False)
    try:
        execute(
            """
            INSERT INTO audit_log (vehicle_id, actor, actor_id, action_type, action_detail, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (vehicle_id, actor, actor_id, action_type, detail),
        )
    except Exception:
        return


def count_audit_logs() -> int:
    row = fetch_one("SELECT COUNT(*) AS total FROM audit_log")
    return int(row["total"]) if row else 0


def list_audit_logs(limit: int, offset: int):
    return fetch_all(
        """
        SELECT al.id,
               al.vehicle_id,
               al.actor,
               al.actor_id,
               al.action_type,
               al.created_at,
               JSON_UNQUOTE(JSON_EXTRACT(al.action_detail, '$.message')) AS message,
               u.username,
               u.full_name
        FROM audit_log al
        LEFT JOIN user u ON al.actor_id = u.id
        ORDER BY al.created_at DESC, al.id DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )
