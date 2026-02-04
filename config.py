"""
Configuration settings for GiHaNotis
Loads environment variables and provides configuration constants
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration from environment variables"""

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'gihanotis')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Admin credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme123')

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Auto-enable secure cookies in production (requires HTTPS)
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'

    # Session timeout (8 hours)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Rate limiting configuration
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True

    @staticmethod
    def validate():
        """Validate that required configuration is present"""
        required = ['DB_PASSWORD', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']
        missing = [key for key in required if not os.getenv(key)]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        if Config.SECRET_KEY == 'dev-secret-key-change-in-production' and Config.FLASK_ENV == 'production':
            raise ValueError("SECRET_KEY must be set in production environment")
