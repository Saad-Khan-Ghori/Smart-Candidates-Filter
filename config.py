import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    ORACLE_USER = os.environ.get("ORACLE_USER", "ems_user")
    ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "abc123")
    ORACLE_DSN = os.environ.get("ORACLE_DSN", "localhost:1521/xe")

    USE_AI_RANKING = os.environ.get("USE_AI_RANKING", "false").lower() in ("1", "true", "yes")
    USE_SEMANTIC_RANKING = os.environ.get("USE_SEMANTIC_RANKING", "false").lower() in ("1", "true", "yes")

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "resumes")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
