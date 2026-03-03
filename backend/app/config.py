from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
USER_DATA_DIR = PROJECT_ROOT / "user_data"
USERS_JSON_PATH = USER_DATA_DIR / "users.json"

SYSTEM_PROMPTS_DIR = PROJECT_ROOT / "backend" / "app" / "database" / "system_prompts"
CHAT_BASIC_PROMPT_PATH = SYSTEM_PROMPTS_DIR / "chat_basic.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
***REMOVED***
***REMOVED***