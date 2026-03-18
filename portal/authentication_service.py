from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.utils import timezone
from .db import get_connection
from .permissions import ALL_PERMISSIONS


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
        conn.commit()
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
        conn.commit()
    finally:
        conn.close()


def is_sql_session_valid(session_token: str) -> bool:
    if not session_token:
        return False

    now_naive = timezone.now().replace(tzinfo=None)

    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT session_token, user_id, expires_at, revoked_at
            FROM sessions
            WHERE session_token = %s
            LIMIT 1
            """,
            (session_token,),
        )
        row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False
    revoked_at = row.get("revoked_at")
    expires_at = row.get("expires_at")
    if revoked_at is not None:
        return False
    if expires_at is None:
        return False
    return now_naive < expires_at


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


def get_all_permissions() -> List[str]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name
            FROM permissions
            ORDER BY name
            """
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def role_has_permission(role_id: int, permission_name: str) -> bool:
    if permission_name not in ALL_PERMISSIONS:
        return False

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM role_permissions rp
            JOIN permissions p ON p.id = rp.permission_id
            WHERE rp.role_id = %s AND p.name = %s
            LIMIT 1
            """,
            (role_id, permission_name),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def get_role(role_id: int) -> Optional[Role]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, name
            FROM roles
            WHERE id = %s
            LIMIT 1
            """,
            (role_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        permissions = get_permissions_for_role(role_id)
        return Role(
            id=row["id"],
            name=row["name"],
            permissions=permissions,
        )
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, role_id, email, first_name, last_name, is_active
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        return User(
            id=row["id"],
            role_id=row["role_id"],
            email=row["email"],
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            is_active=bool(row.get("is_active", True)),
        )
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[User]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, role_id, email, first_name, last_name, is_active
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            ((email or "").strip().lower(),),
        )
        row = cur.fetchone()
        if not row:
            return None

        return User(
            id=row["id"],
            role_id=row["role_id"],
            email=row["email"],
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            is_active=bool(row.get("is_active", True)),
        )
    finally:
        conn.close()


def record_login_history(user_id: int, ip_address: str, user_agent: str, success: bool) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO login_history (user_id, ip_address, user_agent, success)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, ip_address, user_agent, success),
        )
        conn.commit()
    finally:
        conn.close()


def get_login_history_for_user(user_id: int, limit: int = 50) -> List[LoginHistoryEntry]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT user_id, ip_address, user_agent, success, login_at
            FROM login_history
            WHERE user_id = %s
            ORDER BY login_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()

        entries: List[LoginHistoryEntry] = []
        for row in rows:
            entries.append(
                LoginHistoryEntry(
                    user_id=row["user_id"],
                    ip_address=row.get("ip_address") or "",
                    user_agent=row.get("user_agent") or "",
                    success=bool(row.get("success")),
                    created_at=row.get("login_at"),
                )
            )
        return entries
    finally:
        conn.close()


def validate_permissions_table() -> Dict[str, Any]:
    db_permissions = set(get_all_permissions())
    code_permissions = set(ALL_PERMISSIONS)
    missing_in_db = sorted(code_permissions - db_permissions)
    extra_in_db = sorted(db_permissions - code_permissions)
    return {
        "ok": not missing_in_db,
        "missing_in_db": missing_in_db,
        "extra_in_db": extra_in_db,
        "code_count": len(code_permissions),
        "db_count": len(db_permissions),
    }
