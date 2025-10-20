"""
Configuration module for Flask SERP Tracker
Handles environment variables and application settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # SerpApi settings
    SERPAPI_KEY = os.getenv('SERPAPI_KEY')
    SERPAPI_ENGINE = os.getenv('SERPAPI_ENGINE', 'google')
    SERPAPI_LOCATION = os.getenv('SERPAPI_LOCATION', 'United States')
    SERPAPI_RESULTS = int(os.getenv('SERPAPI_RESULTS', '100'))
    
    # reCAPTCHA settings
    RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
    
    # Application settings
    MAX_KEYWORD_LENGTH = int(os.getenv('MAX_KEYWORD_LENGTH', '200'))
    MAX_DOMAIN_LENGTH = int(os.getenv('MAX_DOMAIN_LENGTH', '100'))
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.SERPAPI_KEY:
            raise ValueError("SERPAPI_KEY is required. Please set it in .env file")
        return True
