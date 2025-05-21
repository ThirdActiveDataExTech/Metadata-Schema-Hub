class Config:
    """PostgreSQL config."""
    DB_USER = "admin"
    DB_PASSWORD = "admin"
    DB_HOST = "localhost"
    DB_PORT = "15432"
    DB_NAME = "datagokr"

    # SQLAlchemy 연결 문자열
    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


config = Config()
