from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.user_data_store import UserDataStore, UserDataStoreError


class ProfileService:
    """
    Service layer for loading and updating user profile information.
    """

    def __init__(self, store: Optional[UserDataStore] = None) -> None:
        """
        Initialize profile service with a data store.
        """
        self.store = store or UserDataStore()

    def get_profile(
        self,
        uid: str,
        fallback_user_name: Optional[str] = None,
        fallback_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve user profile and ensure required fields exist.

        If certain fields are missing, fallback values can be applied.
        """
        profile = self.store.read_profile(uid)

        # Ensure UID is always present
        profile["uid"] = str(uid)

        # Apply fallback values if missing
        if profile.get("user_name") in (None, "", "null") and fallback_user_name:
            profile["user_name"] = fallback_user_name
        if profile.get("role") in (None, "", "null") and fallback_role:
            profile["role"] = fallback_role

        # Ensure optional fields exist for frontend consistency
        profile.setdefault("phone", None)
        profile.setdefault("email", None)
        profile.setdefault("name", None)
        profile.setdefault("company_name", None)
        profile.setdefault("region", None)

        return profile

    def update_profile_fields(
        self,
        uid: str,
        *,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        company_name: Optional[str] = None,
        region: Optional[str] = None,
        fallback_user_name: Optional[str] = None,
        fallback_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update selected fields of the user profile.

        Only provided fields will be updated.
        """
        profile = self.get_profile(
            uid,
            fallback_user_name=fallback_user_name,
            fallback_role=fallback_role,
        )

        # Apply updates only if values are explicitly provided
        if phone is not None:
            profile["phone"] = phone
        if email is not None:
            profile["email"] = email
        if name is not None:
            profile["name"] = name
        if company_name is not None:
            profile["company_name"] = company_name
        if region is not None:
            profile["region"] = region

        # Persist updated profile
        self.store.ensure_user_skeleton(uid)
        self.store.write_profile(uid, profile)

        return profile