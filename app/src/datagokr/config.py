import pathlib


class Config:
    """config."""
    LANDING_URL_PREFIX = "https://www.data.go.kr/data/"
    LANDING_URL_SUFFIX = {"standard": "standard", "open": "openapi", "file": "file"}
    OPENSCHEMA_URL_PREFIX = "https://www.data.go.kr/catalog/"
    DCAT_URL_PREFIX = "https://www.data.go.kr/dcat/metadata/"
    SAMPLE_DIR = pathlib.Path(__file__).parent.parent.parent.parent / 'sample'

    # 데이터베이스 연결 정보
    DB_USER = "admin"
    DB_PASSWORD = "admin"
    DB_HOST = "localhost"
    DB_PORT = "15432"
    DB_NAME = "datagokr"

    # SQLAlchemy 연결 문자열
    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


config = Config()
