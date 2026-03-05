# backend/app/services/user_data_store.py

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.config import USER_DATA_DIR, USERS_JSON_PATH

JsonValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class UserDataStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class StorePaths:
    """
    Folder layout (from project_structure.md):

    <project_root>/
      user_data/
        users.json
        user_data/
          <uid>/
            emails/
            documents/
            <uid>_profile.json
        logs/ (unused)
        surveys/ (unused)
    """
    project_root: Path
    user_data_root: Path
    users_json: Path
    user_data_dir: Path



    @staticmethod
    def discover(project_root: Optional[Path] = None) -> "StorePaths":
        user_data_root = USER_DATA_DIR
        users_json = USERS_JSON_PATH
        user_data_dir = user_data_root / "user_data"
        return StorePaths(
            project_root=user_data_root.parent,
            user_data_root=user_data_root,
            users_json=users_json,
            user_data_dir=user_data_dir,
        )


class UserDataStore:
    """
    A tiny JSON-file "database" for demo usage.

    Responsibilities:
      - Locate user_data folders/files
      - Read/write JSON safely (atomic write)
      - Provide helper methods for profile/emails/groups paths

    Note: routers/services should NOT hardcode paths. They should call this store.
    """

    EMAIL_FILE_RE = re.compile(r"^em_(\d{5})\.json$", re.IGNORECASE)

    def __init__(self, project_root: Optional[str] = None) -> None:
        root_path = Path(project_root).resolve() if project_root else None
        self.paths = StorePaths.discover(root_path)

    # -------------------------
    # basic fs helpers
    # -------------------------

    @staticmethod
    def _read_json_file(path: Path) -> JsonValue:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json_atomic(path: Path, data: JsonValue) -> None:
        """
        Atomic-ish write:
          - write to temp file in same directory
          - fsync
          - replace
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = path.with_name(path.name + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)

    # -------------------------
    # global users.json (auth)
    # -------------------------

    def users_json_path(self) -> Path:
        return self.paths.users_json

    def load_users(self) -> List[Dict[str, Any]]:
        """
        Load accounts for login checks (uid/user_name/password_hash/role).
        """
        p = self.paths.users_json
        if not p.exists():
            raise UserDataStoreError(f"users.json not found: {p}")
        data = self._read_json_file(p)
        if not isinstance(data, list):
            raise UserDataStoreError("users.json must be a JSON list")
        return data  # type: ignore[return-value]

    # -------------------------
    # per-user dirs / files
    # -------------------------

    def user_dir(self, uid: str) -> Path:
        return self.paths.user_data_dir / str(uid)

    def ensure_user_skeleton(self, uid: str) -> None:
        """
        Create minimal folders if missing. Safe to call repeatedly.
        """
        udir = self.user_dir(uid)
        (udir / "emails").mkdir(parents=True, exist_ok=True)
        (udir / "documents").mkdir(parents=True, exist_ok=True)

    # -------------------------
    # profile
    # -------------------------

    def profile_path(self, uid: str) -> Path:
        # per your convention: user_data/user_data/<uid>/<uid>_profile.json
        return self.user_dir(uid) / f"{uid}_profile.json"

    def read_profile(self, uid: str) -> Dict[str, Any]:
        """
        If profile missing, returns a minimal default profile (does NOT auto-write).
        """
        p = self.profile_path(uid)
        if not p.exists():
            return {
                "uid": str(uid),
                "user_name": None,
                "role": None,
                "phone": None,
                "email": None,
                "name": None,
            }
        data = self._read_json_file(p)
        if not isinstance(data, dict):
            raise UserDataStoreError(f"profile must be a JSON object: {p}")
        return data  # type: ignore[return-value]

    def write_profile(self, uid: str, profile_obj: Dict[str, Any]) -> None:
        """
        Overwrite profile. Make sure router filters out any sensitive fields (e.g., password_hash).
        """
        # lightweight sanity
        if str(profile_obj.get("uid", uid)) != str(uid):
            raise UserDataStoreError("profile.uid mismatch with requested uid")
        self._write_json_atomic(self.profile_path(uid), profile_obj)

    # -------------------------
    # emails
    # -------------------------

    def emails_dir(self, uid: str) -> Path:
        return self.user_dir(uid) / "emails"

    def email_path(self, uid: str, email_id: str) -> Path:
        # file naming: em_00001.json
        return self.emails_dir(uid) / f"em_{email_id}.json"

    def list_email_ids(self, uid: str) -> List[str]:
        """
        Return ids like ["00001","00002",...], sorted by numeric id ascending.
        """
        d = self.emails_dir(uid)
        if not d.exists():
            return []

        ids: List[Tuple[int, str]] = []
        for p in d.iterdir():
            if not p.is_file():
                continue
            m = self.EMAIL_FILE_RE.match(p.name)
            if not m:
                continue
            sid = m.group(1)
            ids.append((int(sid), sid))

        ids.sort(key=lambda t: t[0])
        return [sid for _, sid in ids]

    def read_email(self, uid: str, email_id: str) -> Dict[str, Any]:
        p = self.email_path(uid, email_id)

        if not p.exists():
            raise UserDataStoreError(f"email not found: {p}")

        raw = p.read_text(encoding="utf-8", errors="replace")
        raw = raw.strip()

        if not raw:
            raise UserDataStoreError(f"Empty JSON file: {p}")

        data = json.loads(raw)

        if not isinstance(data, dict):
            raise UserDataStoreError(f"email must be a JSON object: {p}")

        return data

    def write_email(self, uid: str, email_obj: Dict[str, Any]) -> None:
        """
        Overwrite email file based on email_obj["id"].
        """
        email_id = str(email_obj.get("id") or "")
        if not re.fullmatch(r"\d{5}", email_id):
            raise UserDataStoreError("email_obj.id must be a 5-digit string like '00001'")
            # ---- emails meta (for future "create email") ----

    def emails_meta_path(self, uid: str) -> Path:
        return self.user_dir(uid) / "emails_meta.json"

    def reserve_next_email_id(self, uid: str) -> str:
        """
        Returns a new unique 5-digit ID like "00003".
        Never reuses IDs even if old files are deleted.
        """
        self.ensure_user_skeleton(uid)

        p = self.emails_meta_path(uid)
        meta = {}
        if p.exists():
            try:
                meta = self._read_json_file(p)
            except Exception:
                meta = {}

        next_id = meta.get("next_id")
        if not isinstance(next_id, int) or next_id <= 0:
            ids = self.list_email_ids(uid)
            max_id = max([int(x) for x in ids], default=0)
            next_id = max_id + 1

        meta["next_id"] = next_id + 1
        self._write_json_atomic(p, meta)
        return f"{next_id:05d}"

    def emails_meta_path(self, uid: str) -> Path:
        # user_data/user_data/<uid>/emails_meta.json
        return self.user_dir(uid) / "emails_meta.json"

    def _read_emails_meta(self, uid: str) -> Dict[str, Any]:
        p = self.emails_meta_path(uid)
        if not p.exists():
            return {}
        data = self._read_json_file(p)
        if isinstance(data, dict):
            return data
        return {}

    def _write_emails_meta(self, uid: str, meta: Dict[str, Any]) -> None:
        self._write_json_atomic(self.emails_meta_path(uid), meta)

    def reserve_next_email_id(self, uid: str) -> str:
        """
        Reserve a new unique 5-digit email id.
        This prevents reusing IDs even if old files are deleted.

        Returns: "00001", "00002", ...
        """
        self.ensure_user_skeleton(uid)

        meta = self._read_emails_meta(uid)
        next_id = meta.get("next_id", None)

        if not isinstance(next_id, int) or next_id <= 0:
            # bootstrap from existing files (max+1)
            ids = self.list_email_ids(uid)
            max_id = max([int(x) for x in ids], default=0)
            next_id = max_id + 1

        # reserve current, then increment
        current = next_id
        meta["next_id"] = next_id + 1
        self._write_emails_meta(uid, meta)

        return f"{current:05d}"

    def delete_email(self, uid: str, email_id: str) -> None:
        """
        Delete the email json file from disk: em_00001.json
        """
        if not re.fullmatch(r"\d{5}", str(email_id)):
            raise UserDataStoreError("email_id must be a 5-digit string like '00001'")

        p = self.email_path(uid, email_id)
        if not p.exists():
            raise UserDataStoreError(f"email not found: {p}")

        p.unlink()

    # -------------------------
    # groups (lightweight)
    # -------------------------

    def groups_path(self, uid: str) -> Path:
        """
        Store groups in a single file:
          user_data/user_data/<uid>/groups.json
        """
        return self.user_dir(uid) / "groups.json"

    def read_groups(self, uid: str) -> List[Dict[str, Any]]:
        p = self.groups_path(uid)
        if not p.exists():
            return []
        data = self._read_json_file(p)
        if not isinstance(data, list):
            raise UserDataStoreError(f"groups.json must be a JSON list: {p}")
        # best-effort: keep only dict entries
        return [x for x in data if isinstance(x, dict)]  # type: ignore[return-value]

    def write_groups(self, uid: str, groups: List[Dict[str, Any]]) -> None:
        self._write_json_atomic(self.groups_path(uid), groups)