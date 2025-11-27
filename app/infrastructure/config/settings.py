from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "agape-v3"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str
    DATABASE_READER_URL: Optional[str] = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    # Security & JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRY_MINUTES: int = 10
    REGISTRATION_SESSION_EXPIRY_HOURS: int = 24

    # AWS - General
    AWS_REGION: str = "eu-south-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # AWS S3 - File Storage
    AWS_S3_REGION: str = "eu-south-2"
    AWS_S3_BUCKET: str = ""
    AWS_S3_PROFILE_IMAGES_PREFIX: str = "profile-images/"
    AWS_S3_POST_IMAGES_PREFIX: str = "post-images/"
    AWS_S3_POST_VIDEOS_PREFIX: str = "post-videos/"
    AWS_S3_CHANNEL_IMAGES_PREFIX: str = "channel-images/"
    AWS_S3_EVENT_IMAGES_PREFIX: str = "event-images/"

    # AWS SES - Email
    AWS_SES_REGION: str = "eu-west-1"
    AWS_SES_FROM_EMAIL: str = ""
    AWS_SES_REPLY_TO_EMAIL: Optional[str] = None

    # AWS SNS - SMS
    AWS_SNS_REGION: str = "us-east-1"
    AWS_SNS_SENDER_ID: str = "Agape"

    # Stripe - Payments
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CURRENCY: str = "EUR"

    # Expo Push Notifications
    EXPO_ACCESS_TOKEN: Optional[str] = None

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # File Upload Limits
    MAX_FILE_SIZE_MB: int = 10
    MAX_VIDEO_SIZE_MB: int = 100
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/jpg,image/webp"
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/quicktime,video/x-msvideo"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_image_types_list(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    @property
    def allowed_video_types_list(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_VIDEO_TYPES.split(",")]


settings = Settings()
