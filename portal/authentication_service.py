from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.utils import timezone
from .db import get_connection


@dataclass
class User:
    id: int
    role_id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    def display_name(self) -> str:
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return name or self.email

@dataclass
class Session:
    user_id: int
    session_token: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    def expired_already(self, now: datetime) -> bool:
        if self.revoked_at is not None:
            return True
        return now >= self.expires_at
    def revoke(self) -> None:
        self.revoked_at = datetime.now()


@dataclass
class Permission:
    id: int
    name: str


@dataclass
class Role:
    id: int
    name: str
    permissions: List[str]


@dataclass
class LoginHistoryEntry:
    user_id: int
    ip_address: str
    user_agent: str
    success: bool
    created_at: Optional[datetime] = None


def dict_get(d: Dict[str, Any], key: str, default=None):
    return d[key] if key in d else default

def create_sql_session(user_id: int, session_token: str, hours_valid: int = 2) -> None:
    expires_at = (timezone.now() + timedelta(hours=hours_valid)).replace(tzinfo=None)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, session_token, expires_at),
        )
    finally:
        conn.close()


def revoke_sql_session(session_token: str) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sessions
            SET revoked_at = NOW()
            WHERE session_token = %s AND revoked_at IS NULL
            """,
            (session_token,),
        )
    finally:
        conn.close()


def get_permissions_for_role(role_id: int) -> List[str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.name
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = %s
            ORDER BY p.name
            """,
            (role_id,),
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
