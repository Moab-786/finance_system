import os
from dotenv import load_dotenv

load_dotenv()


def get_settings() -> dict:
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./finance.db"),
        "secret_key": os.getenv("SECRET_KEY", "change-this-secret-key"),
        "token_algorithm": os.getenv("TOKEN_ALGORITHM", "HS256"),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        "default_page_size": int(os.getenv("DEFAULT_PAGE_SIZE", "10")),
        "max_page_size": int(os.getenv("MAX_PAGE_SIZE", "100")),
    }
