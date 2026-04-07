from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.services.auth_instance import auth_service
from app.config import USER_DATA_DIR, USERS_JSON_PATH

JsonValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class UserDataStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class StorePaths:
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
        udir = self.user_dir(uid)
        (udir / "emails").mkdir(parents=True, exist_ok=True)
        (udir / "documents").mkdir(parents=True, exist_ok=True)

    # -------------------------
    # profile
    # -------------------------

    def profile_path(self, uid: str) -> Path:
        return self.user_dir(uid) / "profile.json"

    def read_profile(self, uid: str) -> Dict[str, Any]:
        p = self.profile_path(uid)
        if not p.exists():
            return {
                "uid": str(uid),
                "user_name": None,
                "role": None,
                "phone": None,
                "email": None,
                "name": None,
                "company_name": None,
                "region": None,
            }
        data = self._read_json_file(p)
        if not isinstance(data, dict):
            raise UserDataStoreError(f"profile must be a JSON object: {p}")
        return data  # type: ignore[return-value]

    def write_profile(self, uid: str, profile_obj: Dict[str, Any]) -> None:
        if str(profile_obj.get("uid", uid)) != str(uid):
            raise UserDataStoreError("profile.uid mismatch with requested uid")
        self._write_json_atomic(self.profile_path(uid), profile_obj)

    # -------------------------
    # emails
    # -------------------------

    def emails_dir(self, uid: str) -> Path:
        return self.user_dir(uid) / "emails"

    def email_path(self, uid: str, email_id: str) -> Path:
        return self.emails_dir(uid) / f"em_{email_id}.json"

    def list_email_ids(self, uid: str) -> List[str]:
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

        raw = p.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            raise UserDataStoreError(f"Empty JSON file: {p}")

        data = json.loads(raw)
        if not isinstance(data, dict):
            raise UserDataStoreError(f"email must be a JSON object: {p}")

        return data

    # -------------------------
    # email meta / id allocation
    # -------------------------

    def emails_meta_path(self, uid: str) -> Path:
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

    def find_smallest_available_email_id(self, uid: str) -> str:
        """
        Scan the user's email files and return the smallest available 5-digit ID.

        Examples:
        existing = 00001, 00002, 00004 -> returns 00003
        existing = none -> returns 00001
        """
        self.ensure_user_skeleton(uid)

        used_ids = set()
        for sid in self.list_email_ids(uid):
            if sid.isdigit():
                used_ids.add(int(sid))

        candidate = 1
        while candidate in used_ids:
            candidate += 1

        return f"{candidate:05d}"

    def reserve_next_email_id(self, uid: str) -> str:
        """
        Kept for backward compatibility, but now delegates to the smallest
        available ID policy instead of relying on emails_meta.json.
        """
        return self.find_smallest_available_email_id(uid)

    # -------------------------
    # email write / create / delete
    # -------------------------

    def write_email(self, uid: str, email_obj: Dict[str, Any]) -> None:
        email_id = str(email_obj.get("id") or "")
        if not re.fullmatch(r"\d{5}", email_id):
            raise UserDataStoreError("email_obj.id must be a 5-digit string like '00001'")

        self.ensure_user_skeleton(uid)
        self._write_json_atomic(self.email_path(uid, email_id), email_obj)

    def create_email(self, uid: str, email_obj: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_user_skeleton(uid)

        obj = dict(email_obj)

        # If caller already provides a valid ID, respect it but prevent overwrite.
        existing_id = str(obj.get("id") or "")
        if re.fullmatch(r"\d{5}", existing_id):
            target_path = self.email_path(uid, existing_id)
            if target_path.exists():
                raise UserDataStoreError(f"email id already exists: {existing_id}")
            self.write_email(uid, obj)
            return obj

        # Otherwise allocate the smallest currently available ID.
        candidate = 1
        while True:
            new_id = f"{candidate:05d}"
            target_path = self.email_path(uid, new_id)
            if not target_path.exists():
                obj["id"] = new_id
                self.write_email(uid, obj)
                return obj
            candidate += 1

    def delete_email(self, uid: str, email_id: str) -> None:
        if not re.fullmatch(r"\d{5}", str(email_id)):
            raise UserDataStoreError("email_id must be a 5-digit string like '00001'")

        p = self.email_path(uid, email_id)
        if not p.exists():
            raise UserDataStoreError(f"email not found: {p}")

        p.unlink()

    # -------------------------
    # groups
    # -------------------------

    def groups_path(self, uid: str) -> Path:
        return self.user_dir(uid) / "groups.json"

    def read_groups(self, uid: str) -> List[Dict[str, Any]]:
        p = self.groups_path(uid)
        if not p.exists():
            return []
        data = self._read_json_file(p)
        if not isinstance(data, list):
            raise UserDataStoreError(f"groups.json must be a JSON list: {p}")
        return [x for x in data if isinstance(x, dict)]  # type: ignore[return-value]

    def write_groups(self, uid: str, groups: List[Dict[str, Any]]) -> None:
        self._write_json_atomic(self.groups_path(uid), groups)