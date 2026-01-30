import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'veo_automation')

# Google Flow Credentials
GOOGLE_FLOW_EMAIL = os.environ.get('GOOGLE_FLOW_EMAIL', 'Sameer@techhub.codes')
GOOGLE_FLOW_PASSWORD = os.environ.get('GOOGLE_FLOW_PASSWORD', 'Hhub@#11')
GOOGLE_FLOW_URL = os.environ.get('GOOGLE_FLOW_URL', 'https://labs.google/fx/tools/flow')

# Cloudflare R2 Storage Configuration
CLOUDFLARE_ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
CLOUDFLARE_ACCESS_KEY = os.environ.get('CLOUDFLARE_ACCESS_KEY', '')
CLOUDFLARE_SECRET_KEY = os.environ.get('CLOUDFLARE_SECRET_KEY', '')
CLOUDFLARE_BUCKET_NAME = os.environ.get('CLOUDFLARE_BUCKET_NAME', 'veobucket')
CLOUDFLARE_R2_ENDPOINT = os.environ.get('CLOUDFLARE_R2_ENDPOINT', '')
CLOUDFLARE_R2_TTL_HOURS = int(os.environ.get('CLOUDFLARE_R2_TTL_HOURS', '2'))

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID', '')
TELEGRAM_LOG_CHANNEL = os.environ.get('TELEGRAM_LOG_CHANNEL', '')
TELEGRAM_API_ID = os.environ.get('TELEGRAM_API_ID', '')
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH', '')

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