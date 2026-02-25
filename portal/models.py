from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

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
        # Actual DB update is handled in authentication_service.revoke_sql_session()
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
