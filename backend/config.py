import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'veo_automation')

# Google Flow Credentials (from user)
GOOGLE_FLOW_EMAIL = "Sameer@techhub.codes"
GOOGLE_FLOW_PASSWORD = "Hhub@#11"
GOOGLE_FLOW_URL = "https://labs.google/fx/tools/flow"

# Storage Configuration (Mock credentials for now)
CLOUDFLARE_ACCOUNT_ID = "mock_account_id_123456"
CLOUDFLARE_ACCESS_KEY = "mock_access_key_abcdef"
CLOUDFLARE_SECRET_KEY = "mock_secret_key_xyz789"
CLOUDFLARE_BUCKET_NAME = "veo-videos-temp"
CLOUDFLARE_R2_TTL_HOURS = 2

# Telegram Configuration (Mock credentials)
TELEGRAM_BOT_TOKEN = "mock_bot_token_123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHANNEL_ID = "mock_channel_-1001234567890"
TELEGRAM_API_ID = "mock_api_id_12345678"
TELEGRAM_API_HASH = "mock_api_hash_abcdef1234567890"

# File Storage
TEMP_UPLOAD_DIR = Path("/app/temp_uploads")
TEMP_DOWNLOAD_DIR = Path("/app/temp_downloads")
LOGS_DIR = Path("/app/logs")

# Create directories
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Google Flow Settings
VIDEO_OUTPUTS_PER_PROMPT = 2
ASPECT_RATIO = "portrait"
MODEL_NAME = "Veo 3.1 - Fast [Lower Priority]"
DOWNLOAD_QUALITY = "720p"

# Error Retry Configuration
HIGH_DEMAND_RETRY_DELAY_SECONDS = 180  # 3 minutes
MAX_RETRY_ATTEMPTS = 5
GENERATION_POLL_INTERVAL_SECONDS = 10

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')