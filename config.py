import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file for local development
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Check if .env is missing but we are running locally (not in CI)
    if not os.getenv("CI") and not os.getenv("GITHUB_ACTIONS"):
        print("WARNING: .env file not found. If running locally, please copy .env.example to .env and configure it.", file=sys.stderr)

# Gmail Secrets
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Recipient Email (defaults to sender if not explicitly configured)
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL") or GMAIL_USER

# Recipe API Key
RECIPE_API_KEY = os.getenv("RECIPE_API_KEY")

# Determine Mock Mode:
# Enable mock mode if no recipe api key is provided, or if it is a placeholder.
IS_MOCK_MODE = not RECIPE_API_KEY or RECIPE_API_KEY.strip() in ("", "your_api_key_here")

# Validate required variables
def validate_config():
    """Validates that necessary configuration settings are present at startup."""
    errors = []
    
    if not GMAIL_USER:
        errors.append("GMAIL_USER is not set. Please specify your Gmail address.")
    if not GMAIL_APP_PASSWORD:
        errors.append("GMAIL_APP_PASSWORD is not set. Please specify your Gmail App Password.")
        
    if errors:
        print("\n=== CONFIGURATION ERROR ===", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        print("\nSetup Instructions:\n"
              "1. Copy .env.example to .env\n"
              "2. Set your GMAIL_USER and GMAIL_APP_PASSWORD in the .env file.\n"
              "3. For production, set these as Repository Secrets in GitHub (Settings -> Secrets -> Actions).\n"
              "===========================\n", file=sys.stderr)
        raise ValueError("Missing critical email configuration. See error details above.")

# Application Constants
CALORIE_TARGET_PERSON_A = 2500.0
CALORIE_TARGET_PERSON_B = 2000.0
TOTAL_CALORIE_TARGET = CALORIE_TARGET_PERSON_A + CALORIE_TARGET_PERSON_B

# Ratio of calories: A receives 55.6%, B receives 44.4%
PORTION_RATIO_A = CALORIE_TARGET_PERSON_A / TOTAL_CALORIE_TARGET
PORTION_RATIO_B = CALORIE_TARGET_PERSON_B / TOTAL_CALORIE_TARGET

# Calorie distribution per meal type (based on common dietary standards)
MEAL_CALORIE_ALLOCATION = {
    "breakfast": 0.22,  # 22% -> ~1000 kcal combined
    "lunch": 0.39,      # 39% -> ~1750 kcal combined
    "dinner": 0.39      # 39% -> ~1750 kcal combined
}

# History file
HISTORY_FILE = "meal_history.json"
