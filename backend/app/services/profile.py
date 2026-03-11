from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.user_data_store import UserDataStore, UserDataStoreError


class ProfileService:
    def __init__(self, store: Optional[UserDataStore] = None) -> None:
        self.store = store or UserDataStore()

    def get_profile(
        self,
        uid: str,
        fallback_user_name: Optional[str] = None,
        fallback_role: Optional[str] = None
    ) -> Dict[str, Any]:
        profile = self.store.read_profile(uid)

        profile["uid"] = str(uid)

        if profile.get("user_name") in (None, "", "null") and fallback_user_name:
            profile["user_name"] = fallback_user_name
        if profile.get("role") in (None, "", "null") and fallback_role:
            profile["role"] = fallback_role

        profile.setdefault("phone", None)
        profile.setdefault("email", None)
        profile.setdefault("name", None)
        profile.setdefault("region", None)

        return profile

    def update_profile_fields(
        self,
        uid: str,
        *,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        region: Optional[str] = None,
        fallback_user_name: Optional[str] = None,
        fallback_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        profile = self.get_profile(
            uid,
            fallback_user_name=fallback_user_name,
            fallback_role=fallback_role,
        )

        if phone is not None:
            profile["phone"] = phone
        if email is not None:
            profile["email"] = email
        if name is not None:
            profile["name"] = name
        if region is not None:
            profile["region"] = region

        self.store.ensure_user_skeleton(uid)
        self.store.write_profile(uid, profile)
        return profile