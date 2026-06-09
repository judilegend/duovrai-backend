import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors_origins(v: Union[str, List[str]]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v
    return []

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Duovrai Backend"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], 
        BeforeValidator(parse_cors_origins)
    ] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "sqlite:///./duovrai.db"

    # Stripe
    STRIPE_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:5173/success?session_id={CHECKOUT_SESSION_ID}"
    STRIPE_CANCEL_URL: str = "http://localhost:5173/pricing-page"
    
    # Price IDs (Configured in Stripe for 9,90€ and 19,90€)
    STRIPE_PRICE_ESSENTIEL: str = ""
    STRIPE_PRICE_PREMIUM: str = ""

    # Anthropic Claude API
    ANTHROPIC_API_KEY: str = ""

    # SMTP Configuration
    SMTP_HOST: str = "smtp.resend.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "resend"
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "reports@duovrai.com"
    SMTP_FROM_NAME: str = "Duovrai - Analyse Amoureuse"

    # Default admin credentials
    ADMIN_EMAIL: str = "admin@duovrai.com"
    ADMIN_PASSWORD: str = "admin@2026"
    ADMIN_FULL_NAME: str = "Duovrai Admin"

    # JWT Secret Key
    SECRET_KEY: str = "51TSK3NFWwuVJ3DHFINF4KYTJnDiOoINPg7T96t91DZb7w8oyVUsZalcF6pqmjXIhVYXqsWeJFZ4w5mrfpuWOD7RD00KK0sI0GR"

    # PDF Output Storage Path
    PDF_OUTPUT_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "storage", "reports"
    )

settings = Settings()

# Normalize PDF_OUTPUT_DIR: if the environment provided a relative path
# (for example "./storage/reports"), resolve it against the project root
# so runtime always writes into the repository instead of an arbitrary CWD.
if settings.PDF_OUTPUT_DIR and not os.path.isabs(settings.PDF_OUTPUT_DIR):
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    settings.PDF_OUTPUT_DIR = os.path.abspath(
        os.path.join(_project_root, settings.PDF_OUTPUT_DIR)
    )

