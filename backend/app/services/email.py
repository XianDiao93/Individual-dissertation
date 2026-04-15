from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.user_data_store import UserDataStore, UserDataStoreError


class EmailService:
    """
    Service layer for reading, normalizing, updating, and deleting email records.
    """

    def __init__(self, store: Optional[UserDataStore] = None) -> None:
        """
        Initialize email service with a data store.
        """
        self.store = store or UserDataStore()

    def list_emails(
        self,
        uid: str,
        *,
        archived: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of email summary dicts.

        archived:
          - None: all
          - False: only unarchived (group_id is null)
          - True: only archived (group_id not null)

        Emails are sorted by numeric ID in descending order.
        """
        ids = self.store.list_email_ids(uid)

        # Sort latest-first by numeric ID
        ids_sorted = sorted(ids, key=lambda x: int(x), reverse=True)

        out: List[Dict[str, Any]] = []
        for eid in ids_sorted:
            try:
                e = self.store.read_email(uid, eid)
            except UserDataStoreError:
                continue

            group_id = e.get("group_id", None)
            is_archived = group_id is not None

            if archived is True and not is_archived:
                continue
            if archived is False and is_archived:
                continue

            risk = e.get("risk") or {}
            risk_level = risk.get("level") or "unknown"
            risk_tags = risk.get("tags") or risk.get("flags") or []

            out.append(
                {
                    "id": e.get("id", eid),
                    "subject": e.get("subject", None),
                    "from": e.get("from", None),
                    "status": e.get("status", "draft"),
                    "group_id": group_id,
                    "risk_level": risk_level,
                    "risk_tags": risk_tags,
                }
            )

        return out

    def get_email(self, uid: str, email_id: str) -> Dict[str, Any]:
        """
        Return a full email record with required default fields added if missing.
        """
        e = self.store.read_email(uid, email_id)

        # Ensure required top-level fields exist
        e.setdefault("id", email_id)
        e.setdefault("source_region", None)
        e.setdefault("language", None)
        e.setdefault("subject", None)
        e.setdefault("reply", None)
        e.setdefault("group_id", None)
        e.setdefault("from", None)
        e.setdefault("status", "draft")

        # Normalize risk structure
        risk = e.get("risk")
        if not isinstance(risk, dict):
            risk = {}
        risk.setdefault("level", "unknown")
        if not isinstance(risk.get("tags"), list):
            risk["tags"] = risk.get("tags") or risk.get("flags") or []
        risk.setdefault("summary", None)
        e["risk"] = risk

        return e

    def update_email(self, uid: str, email_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a lightweight patch update to an email record.

        Only whitelisted fields can be updated.
        """
        e = self.get_email(uid, email_id)

        allowed_fields = {
            "source_region",
            "language",
            "subject",
            "reply",
            "group_id",
            "from",
            "status",
            "risk",
        }

        for k, v in patch.items():
            if k in allowed_fields:
                e[k] = v

        # Write updated record back to storage
        self.store.ensure_user_skeleton(uid)
        self.store.write_email(uid, e)
        return e

    def delete_email(self, uid: str, email_id: str) -> None:
        """
        Delete an email record by ID.
        """
        self.store.delete_email(uid, email_id)