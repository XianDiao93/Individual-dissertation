from pathlib import Path
import os

# Root directory of the project (two levels above this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# -------------------------
# Data directories
# -------------------------

# General data directory (e.g. templates, raw data, processed data)
DATA_DIR = PROJECT_ROOT / "data"

# User-specific storage directory (profiles, emails, documents)
USER_DATA_DIR = PROJECT_ROOT / "user_data"

# Global user authentication file
USERS_JSON_PATH = USER_DATA_DIR / "users.json"

# -------------------------
# System prompt configuration
# -------------------------

# Directory containing system prompt JSON files
SYSTEM_PROMPTS_DIR = PROJECT_ROOT / "backend" / "app" / "database" / "system_prompts"

# Prompt for communication generation
CHAT_BASIC_PROMPT_PATH = SYSTEM_PROMPTS_DIR / "chat_basic.json"

# Prompt for document generation
DOC_BASIC_PROMPT_PATH = SYSTEM_PROMPTS_DIR / "doc_basic.json"

# -------------------------
# Environment / API config
# -------------------------

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Fail fast if API key is not provided
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")