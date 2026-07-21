"""Environment-driven configuration with safe local defaults."""
import os


class Settings:
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-change-me")
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "120"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./registry.db")
    redis_url: str = os.getenv("REDIS_URL", "")            # empty -> in-memory cache
    preview_grpc_target: str = os.getenv("PREVIEW_GRPC_TARGET", "")  # empty -> in-process
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "")          # empty -> registry-only


settings = Settings()
