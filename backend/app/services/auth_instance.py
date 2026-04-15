# backend/app/services/auth_instance.py

from app.config import USERS_JSON_PATH
from app.services.auth import AuthService

"""
Singleton instance of AuthService.

This ensures that:
- session tokens are stored in a shared in-memory store
- tokens remain valid across different routers and requests
- users do not get logged out when switching pages
"""

auth_service = AuthService(USERS_JSON_PATH)