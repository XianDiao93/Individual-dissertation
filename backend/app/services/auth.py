# backend/app/services/auth.py

# backend/app/services/auth.py

from __future__ import annotations

import json
import os
import time
import secrets
import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

# ---------------------------
# Password hashing / verify
# ---------------------------

ALGO = "pbkdf2_sha256"
DEFAUT_ITERATIONS = 260_000  # 保留不影响验证（验证时从 stored 字符串解析）


def _b64_decode_nopad(s: str) -> bytes:
    s_padded = s + "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s_padded.encode("ascii"))


def verify_password(password: str, stored: str) -> bool:
    """
    Verify password against stored hash string:
    pbkdf2_sha256$260000$<salt_b64>$<hash_b64>
    """
    try:
        algo, iters_str, salt_b64, hash_b64 = stored.split("$", 3)
        if algo != ALGO:
            return False

        iterations = int(iters_str)
        salt = _b64_decode_nopad(salt_b64)
        expected = _b64_decode_nopad(hash_b64)

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ---------------------------
# Auth service
# ---------------------------

@dataclass(frozen=True)
class AuthUser:
    user_id: str
    user_name: str
    role: str


class AuthService:
    """
    Minimal auth service:
    - load users from users.json
    - verify password
    - issue random token
    - keep token->user mapping in memory
    """

    def __init__(self, users_json_path: str, token_ttl_seconds: int = 24 * 3600) -> None:
        self.users_json_path = users_json_path
        self.token_ttl_seconds = token_ttl_seconds

        # token -> (AuthUser, issued_at_epoch)
        self._sessions: Dict[str, Tuple[AuthUser, int]] = {}

    # ---- users ----

    def _load_users(self) -> list[dict[str, Any]]:
        if not os.path.exists(self.users_json_path):
            raise FileNotFoundError(f"users.json not found: {self.users_json_path}")

        with open(self.users_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("users.json must be a JSON list of user objects")
        return data

    def _find_user_record_by_name(self, user_name: str) -> Optional[dict[str, Any]]:
        users = self._load_users()
        for u in users:
            if str(u.get("user_name")) == str(user_name):
                return u
        return None

    # ---- sessions ----

    def _cleanup_expired(self) -> None:
        now = int(time.time())
        expired = [t for t, (_, ts) in self._sessions.items() if now - ts > self.token_ttl_seconds]
        for t in expired:
            self._sessions.pop(t, None)

    def login(self, user_name: str, password: str) -> dict[str, Any]:
        """
        Returns:
          success: {"ok": True, "token": "...", "role": "...", "user_name": "..."}
          failure: {"ok": False, "error": "invalid_credentials"}
        """
        self._cleanup_expired()

        rec = self._find_user_record_by_name(user_name)
        if not rec:
            return {"ok": False, "error": "invalid_credentials"}

        stored_hash = rec.get("password_hash")
        role = rec.get("role")
        user_id = rec.get("user_id")
        stored_user_name = rec.get("user_name")

        if not isinstance(stored_hash, str) or not isinstance(role, str) or not isinstance(user_id, str) or not isinstance(stored_user_name, str):
            return {"ok": False, "error": "invalid_credentials"}

        if not verify_password(password, stored_hash):
            return {"ok": False, "error": "invalid_credentials"}

        token = secrets.token_urlsafe(32)
        user = AuthUser(user_id=user_id, user_name=stored_user_name, role=role)
        self._sessions[token] = (user, int(time.time()))

        return {"ok": True, "token": token, "role": role, "user_name": stored_user_name}

    def get_current_user(self, token: str) -> Optional[AuthUser]:
        self._cleanup_expired()

        entry = self._sessions.get(token)
        if not entry:
            return None

        user, issued_at = entry
        now = int(time.time())
        if now - issued_at > self.token_ttl_seconds:
            self._sessions.pop(token, None)
            return None

        return user

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)

