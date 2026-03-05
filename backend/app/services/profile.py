# backend/app/services/profile.py

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.user_data_store import UserDataStore, UserDataStoreError


class ProfileService:
    """
    Thin service around UserDataStore.
    """

    def __init__(self, store: Optional[UserDataStore] = None) -> None:
        self.store = store or UserDataStore()

    def get_profile(self, uid: str, fallback_user_name: Optional[str] = None, fallback_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Read profile from disk. If missing, return a default profile object (not auto-written).
        Also fill user_name/role from auth as fallback to make UI nicer.
        """
        profile = self.store.read_profile(uid)

        # Ensure required field
        profile["uid"] = str(uid)

        # Optional fallback from auth/session
        if profile.get("user_name") in (None, "", "null") and fallback_user_name:
            profile["user_name"] = fallback_user_name
        if profile.get("role") in (None, "", "null") and fallback_role:
            profile["role"] = fallback_role

        # Ensure demo fields exist (so frontend doesn't need many ifs)
        profile.setdefault("phone", None)
        profile.setdefault("email", None)
        profile.setdefault("name", None)

        return profile

    def update_profile_fields(
        self,
        uid: str,
        *,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        fallback_user_name: Optional[str] = None,
        fallback_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update only phone/email/name. Keep uid stable.
        """
        profile = self.get_profile(uid, fallback_user_name=fallback_user_name, fallback_role=fallback_role)

        # Only update if provided (None means "no change" for demo)
        if phone is not None:
            profile["phone"] = phone
        if email is not None:
            profile["email"] = email
        if name is not None:
            profile["name"] = name

        # Write back
        self.store.ensure_user_skeleton(uid)
        self.store.write_profile(uid, profile)
        return profile