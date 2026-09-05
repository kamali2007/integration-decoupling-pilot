import os
from pathlib import Path

# Base directories using pathlib to avoid hardcoded OS-specific paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

# SQLite database file location
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'integration_pilot.db'}")

# CORS settings
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

# Business Rule defaults (CR-001)
DEFAULT_URGENT_QTY_THRESHOLD = 100
UPDATED_URGENT_QTY_THRESHOLD = 200

# Retry policy defaults
MAX_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SEC = 2
