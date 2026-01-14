# Database
DB_FILE = "lol_pro_stats.db"

# Leaguepedia API
API_BASE_URL = "https://lol.fandom.com/api.php"
API_USER_AGENT = "LoLProStatsApp/1.0 (Educational Project)"

# Bot credentials for Leaguepedia API (required for cargo queries)
BOT_USERNAME = "Joshiro2@joshiro2"
BOT_PASSWORD = "nt7d3cf1hvk2ibkka76030udifbs0td1"

# Rate limiting
API_REQUEST_DELAY = 0.5  # Seconds between API requests
API_MAX_LIMIT = 500  # Max results per query
API_MAX_RETRIES = 5  # Retry failed queries

# Default filters
DEFAULT_TOURNAMENT = "LCK"
DEFAULT_YEAR = "2025"

# Application settings
APP_TITLE = "LoL Pro Player Stats System"
APP_MIN_WIDTH = 1000
APP_MIN_HEIGHT = 650

DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin"

import sys
import os

def resolved_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    PyInstaller unpacks data to sys._MEIPASS
    """
    if hasattr(sys, 'frozen'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_db_path_file() -> str:
    """
    Get path to DB file.
    In frozen mode, DB should be next to executable (or in user data), 
    NOT in _MEIPASS (which is temporary/read-only).
    """
    if hasattr(sys, 'frozen'):
        # In frozen mode, put DB next to executable
        base_path = os.path.dirname(sys.executable)
    else:
        # In dev mode, put DB in project root
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, DB_FILE)

