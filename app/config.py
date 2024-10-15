from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application settings with different environments."""
    
    MONGO_URI: str
    MONGO_DB_NAME: str

    SENDGRID_API_KEY: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    TWILIO_SMS_NUMBER: str

    ALLOWED_ORIGINS: list[str]

    class Config:
        """Load environment-specific configurations."""
        env_file = ".env"  # Default is .env, can be overridden below

# Load different env files based on the environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    settings = Settings(_env_file=".env.cloud")
else:
    settings = Settings(_env_file=".env.local")
