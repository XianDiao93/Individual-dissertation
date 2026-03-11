from app.config import USERS_JSON_PATH
from app.services.auth import AuthService

auth_service = AuthService(USERS_JSON_PATH)