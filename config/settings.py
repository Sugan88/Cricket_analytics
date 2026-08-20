"""
Configuration Management for Cricket Analytics
Handles settings, API keys, and environment variables
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===================== DATABASE CONFIGURATION =====================
class DatabaseConfig:
    """PostgreSQL Database settings"""
    
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'cricket_analytics')
    
    # Connection string for SQLAlchemy
    DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # Connection pool settings
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_RECYCLE = 3600


# ===================== CRICKET DATA SETTINGS =====================
class CricketDataConfig:
    """Settings for cricket data"""
    
    # Australian Players to track (sample)
    AUSTRALIAN_PLAYERS = {
        'Steve Smith': 267192,
        'Pat Cummins': 346871,
        'David Warner': 253802,
        'Josh Hazlewood': 347442,
        'Nathan Lyon': 419841,
        'Usman Khawaja': 299849,
        'Travis Head': 334743,
        'Scott Boland': 370478,
    }
    
    # Countries to track
    COUNTRIES = {
        'Australia': 'AUS',
        'India': 'IND',
        'England': 'ENG',
        'Pakistan': 'PAK',
        'New Zealand': 'NZL',
    }
    
    # Cricket formats
    FORMATS = ['Test', 'ODI', 'T20']
    
    # Conditions to analyze
    CONDITIONS = {
        'location': ['Home', 'Away'],
        'pitch_type': ['Fast', 'Spinning', 'Seaming', 'Flat'],
        'opponent': ['India', 'England', 'Pakistan', 'West Indies'],
    }


# ===================== ANALYTICS SETTINGS =====================
class AnalyticsConfig:
    """Settings for analytics calculations"""
    
    # Minimum matches for statistical validity
    MIN_MATCHES_THRESHOLD = 5
    
    # Form calculation
    RECENT_FORM_MATCHES = 10
    FORM_WINDOW_SIZES = [5, 10, 20]  # Last 5, 10, 20 matches
    
    # Thresholds for recommendations
    AVERAGE_WARNING_THRESHOLD = 0.8  # 80% of peer average
    CONSISTENCY_WARNING = 25  # Standard deviation
    
    # Peer benchmarks (typical values for good players)
    PEER_BENCHMARKS = {
        'batting_average': 40,
        'strike_rate': 55,
        'bowling_average': 28,
        'economy_rate': 3.2,
    }


# ===================== LOGGING CONFIGURATION =====================
class LoggingConfig:
    """Logging setup"""
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/cricket_analytics.log'
    
    @staticmethod
    def setup_logging():
        """Configure logging for the application"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=LoggingConfig.LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LoggingConfig.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)


# ===================== ENVIRONMENT SETTINGS =====================
class AppConfig:
    """Application-wide settings"""
    
    ENV = os.getenv('ENV', 'development')
    DEBUG = ENV == 'development'
    TIMEZONE = os.getenv('TIMEZONE', 'Australia/Perth')
    
    # API settings
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 2


# ===================== INITIALIZATION =====================
if __name__ == "__main__":
    # Test configuration
    print("=" * 60)
    print("CRICKET ANALYTICS - CONFIGURATION CHECK")
    print("=" * 60)
    print(f"\n✓ Database: {DatabaseConfig.DB_NAME}")
    print(f"✓ Host: {DatabaseConfig.DB_HOST}")
    print(f"✓ Environment: {AppConfig.ENV}")
    print(f"✓ Timezone: {AppConfig.TIMEZONE}")
    print(f"✓ Australian Players: {len(CricketDataConfig.AUSTRALIAN_PLAYERS)}")
    print(f"✓ Countries to Track: {len(CricketDataConfig.COUNTRIES)}")
    print("\n✓ Configuration loaded successfully!\n")