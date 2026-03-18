from __future__ import annotations
import bcrypt
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .db import get_connection
from .authentication_service import record_login_history

class SQLBcryptBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        email_val = (email or username or "").strip().lower()
        if not email_val or not password:
            return None
        ip_address = ""
        user_agent = ""
        if request is not None:
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                ip_address = xff.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR", "") or ""
            user_agent = request.META.get("HTTP_USER_AGENT", "") or ""
        row = None
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT id, role_id, email, password_hash, first_name, last_name, is_active
                FROM users
                WHERE LOWER(email) = %s
                LIMIT 1
                """,
                (email_val,),
            )
            row = cur.fetchone()
        finally:
            if conn:
                conn.close()
        if not row:
            return None
        sql_user_id = int(row["id"])
        role_id = int(row["role_id"])
        is_active = bool(row.get("is_active", True))
        if not is_active:
            record_login_history(
                user_id=sql_user_id,
                ip_address=ip_address,
                user_agent=(user_agent or "")[:255],
                success=False,
            )
            return None
        stored_hash = row.get("password_hash")
        if not stored_hash or not isinstance(stored_hash, str) or not stored_hash.startswith("$2"):
            record_login_history(
                user_id=sql_user_id,
                ip_address=ip_address,
                user_agent=(user_agent or "")[:255],
                success=False,
            )
            return None
        try:
            ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            ok = False
        record_login_history(
            user_id=sql_user_id,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:255],
            success=ok,
        )
        if not ok:
            return None
        django_user, _ = User.objects.get_or_create(
            username=email_val,
            defaults={
                "email": email_val,
                "first_name": row.get("first_name") or "",
                "last_name": row.get("last_name") or "",
                "is_active": True,
            },
        )

        fn = row.get("first_name") or ""
        ln = row.get("last_name") or ""
        updated = False
        if django_user.email != email_val:
            django_user.email = email_val
            updated = True
        if django_user.first_name != fn:
            django_user.first_name = fn
            updated = True
        if django_user.last_name != ln:
            django_user.last_name = ln
            updated = True
        if not django_user.is_active:
            django_user.is_active = True
            updated = True
        if updated:
            django_user.save()
        django_user.sql_user_id = sql_user_id
        django_user.sql_role_id = role_id
        return django_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
