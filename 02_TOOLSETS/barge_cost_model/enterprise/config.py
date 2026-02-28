"""
Enterprise Configuration Management
====================================

Centralized configuration for production deployment including:
- Database connections
- API settings
- Authentication credentials
- Data update schedules
- Logging configuration

Author: Barge Economics Research Team
Date: February 3, 2026
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import json

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "forecasting" / "data"
MODELS_DIR = BASE_DIR / "forecasting" / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration"""

    # PostgreSQL settings (production)
    db_type: str = "postgresql"
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "barge_forecasting")
    username: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")

    # SQLite settings (development)
    sqlite_path: str = str(BASE_DIR / "enterprise" / "barge_forecasting.db")

    def get_connection_string(self, use_sqlite: bool = False) -> str:
        """Generate database connection string"""
        if use_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        else:
            return f"{self.db_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

# ============================================================================
# API CONFIGURATION
# ============================================================================

@dataclass
class APIConfig:
    """API server configuration"""

    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("API_DEBUG", "False").lower() == "true"
    workers: int = int(os.getenv("API_WORKERS", "4"))

    # CORS settings
    cors_origins: list = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # API versioning
    api_version: str = "v1"
    api_prefix: str = "/api/v1"

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]  # Allow all in development

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

@dataclass
class AuthConfig:
    """Authentication and authorization configuration"""

    # JWT settings
    secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Session settings
    session_timeout_minutes: int = 60

    # Password requirements
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True

    # User roles
    default_role: str = "viewer"
    available_roles: list = None

    def __post_init__(self):
        if self.available_roles is None:
            self.available_roles = ["admin", "analyst", "viewer"]

# ============================================================================
# DATA UPDATE CONFIGURATION
# ============================================================================

@dataclass
class DataUpdateConfig:
    """Configuration for automated data updates"""

    # USDA AMS API settings
    usda_api_url: str = "https://mymarketnews.ams.usda.gov/public_data"
    usda_api_key: Optional[str] = os.getenv("USDA_API_KEY")

    # USACE river gauge API
    usace_api_url: str = "https://waterdata.usgs.gov/nwis"
    usace_api_key: Optional[str] = os.getenv("USACE_API_KEY")

    # EIA fuel price API
    eia_api_url: str = "https://api.eia.gov/v2"
    eia_api_key: Optional[str] = os.getenv("EIA_API_KEY")

    # Update schedule (cron format)
    daily_update_time: str = "06:00"  # 6 AM daily
    update_timezone: str = "America/Chicago"

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 300  # 5 minutes

    # Data validation
    validate_on_update: bool = True
    backup_before_update: bool = True

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

@dataclass
class ModelConfig:
    """Model training and inference configuration"""

    # VAR model settings
    var_max_lag: int = 10
    var_information_criterion: str = "aic"

    # SpVAR settings
    spvar_spatial_weighting: str = "inverse_distance"
    spvar_normalize_weights: bool = True

    # Retraining schedule
    retrain_frequency_days: int = 7  # Weekly retraining
    min_observations_for_retrain: int = 100

    # Forecast settings
    forecast_horizons: list = None
    confidence_levels: list = None

    # Model storage
    save_model_history: bool = True
    max_model_versions: int = 10

    def __post_init__(self):
        if self.forecast_horizons is None:
            self.forecast_horizons = [1, 2, 3, 4, 5]
        if self.confidence_levels is None:
            self.confidence_levels = [0.80, 0.90, 0.95]

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

@dataclass
class LoggingConfig:
    """Logging configuration"""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"

    # Log files
    app_log_file: str = str(LOGS_DIR / "app.log")
    api_log_file: str = str(LOGS_DIR / "api.log")
    data_update_log_file: str = str(LOGS_DIR / "data_updates.log")
    model_log_file: str = str(LOGS_DIR / "model_training.log")

    # Rotation settings
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5

    # Performance logging
    log_slow_queries: bool = True
    slow_query_threshold_ms: int = 1000

# ============================================================================
# ALERT CONFIGURATION
# ============================================================================

@dataclass
class AlertConfig:
    """Alert and notification configuration"""

    # Email settings
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@bargeforecasting.com")

    # Alert thresholds
    forecast_error_threshold_pct: float = 30.0  # MAPE > 30%
    data_missing_threshold_days: int = 3
    model_performance_degradation_pct: float = 10.0

    # Alert recipients
    admin_emails: list = None
    analyst_emails: list = None

    # Alert frequency limits
    max_alerts_per_hour: int = 10
    min_time_between_same_alert_minutes: int = 60

    def __post_init__(self):
        if self.admin_emails is None:
            self.admin_emails = []
        if self.analyst_emails is None:
            self.analyst_emails = []

# ============================================================================
# MASTER CONFIGURATION CLASS
# ============================================================================

class Config:
    """Master configuration class combining all settings"""

    def __init__(self, environment: str = "development"):
        self.environment = environment

        # Initialize all configuration sections
        self.database = DatabaseConfig()
        self.api = APIConfig()
        self.auth = AuthConfig()
        self.data_update = DataUpdateConfig()
        self.model = ModelConfig()
        self.logging = LoggingConfig()
        self.alert = AlertConfig()

        # Environment-specific overrides
        if environment == "production":
            self._apply_production_settings()
        elif environment == "testing":
            self._apply_testing_settings()

    def _apply_production_settings(self):
        """Apply production-specific settings"""
        self.api.debug = False
        self.api.cors_origins = ["https://yourdomain.com"]
        self.auth.secret_key = os.getenv("JWT_SECRET_KEY_PROD")
        self.logging.log_level = "WARNING"

    def _apply_testing_settings(self):
        """Apply testing-specific settings"""
        self.api.debug = True
        self.database.sqlite_path = ":memory:"
        self.data_update.validate_on_update = False
        self.logging.log_level = "DEBUG"

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment,
            "database": self.database.__dict__,
            "api": self.api.__dict__,
            "auth": self.auth.__dict__,
            "data_update": self.data_update.__dict__,
            "model": self.model.__dict__,
            "logging": self.logging.__dict__,
            "alert": self.alert.__dict__
        }

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'Config':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)

        config = cls(environment=config_dict.get("environment", "development"))

        # Update from loaded dict
        for section, values in config_dict.items():
            if section != "environment" and hasattr(config, section):
                section_obj = getattr(config, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

        return config

# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================

# Get environment from env variable or default to development
ENVIRONMENT = os.getenv("APP_ENV", "development")

# Create global config instance
config = Config(environment=ENVIRONMENT)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config() -> Config:
    """Get global configuration instance"""
    return config

def reload_config():
    """Reload configuration (useful for testing)"""
    global config
    config = Config(environment=ENVIRONMENT)
    return config

def validate_config() -> list:
    """Validate configuration and return list of issues"""
    issues = []

    # Check critical settings
    if config.auth.secret_key == "change-this-in-production" and config.environment == "production":
        issues.append("JWT secret key must be changed in production")

    if not config.data_update.usda_api_key and config.environment == "production":
        issues.append("USDA API key not configured")

    if not config.alert.admin_emails and config.environment == "production":
        issues.append("No admin email addresses configured for alerts")

    # Check database connectivity (would need actual connection test)
    # issues.append("Database connection test not implemented")

    return issues

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Print current configuration
    print("=" * 70)
    print("ENTERPRISE CONFIGURATION")
    print("=" * 70)
    print(f"\nEnvironment: {config.environment}")
    print(f"\nDatabase: {config.database.get_connection_string(use_sqlite=True)}")
    print(f"API Host: {config.api.host}:{config.api.port}")
    print(f"API Prefix: {config.api.api_prefix}")
    print(f"\nAuth Token Expiry: {config.auth.access_token_expire_minutes} minutes")
    print(f"Available Roles: {config.auth.available_roles}")
    print(f"\nData Update Time: {config.data_update.daily_update_time}")
    print(f"Model Retrain Frequency: {config.model.retrain_frequency_days} days")
    print(f"\nLog Level: {config.logging.log_level}")
    print(f"Log Files: {LOGS_DIR}")

    # Validate configuration
    print("\n" + "=" * 70)
    print("CONFIGURATION VALIDATION")
    print("=" * 70)

    issues = validate_config()
    if issues:
        print("\n⚠ Configuration Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Configuration valid")

    # Save example configuration
    config_file = BASE_DIR / "enterprise" / "config.example.json"
    config.save_to_file(str(config_file))
    print(f"\n✓ Example configuration saved to: {config_file}")
