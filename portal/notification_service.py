from __future__ import annotations
from typing import List, Dict, Any, Optional
from .db import get_connection

def get_unread_count(user_id: int) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,),
        )
        (count,) = cur.fetchone()
        return int(count)
    finally:
        conn.close()

def list_notifications(user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        sql = """
            SELECT id, user_id, category, message, created_at, is_read, read_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        params = [user_id]
        if limit is not None:
            sql += " LIMIT %s"
            params.append(limit)
        cur.execute(sql, tuple(params))
        return cur.fetchall()
    finally:
        conn.close()

def mark_read(user_id: int, notif_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE notifications
            SET is_read = 1, read_at = NOW()
            WHERE id = %s AND user_id = %s
            """,
            (notif_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def mark_all_read(user_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE notifications
            SET is_read = 1, read_at = NOW()
            WHERE user_id = %s AND is_read = 0
            """,
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()
