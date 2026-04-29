import logging
import re
from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import AnyUrl, BeforeValidator, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> Union[List[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list) or isinstance(v, str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # Environment: local, staging, production
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    PORT: int = 8000
    SERVICE_NAME: str = "Active Metadata Management"
    SERVICE_CODE: int = 100
    MAJOR_VERSION: str = "v1"
    STATUS: str = "dev"
    STATIC_DIRECTORY: str = "./static"

    # Request Server URL
    SERVER_URL: str = ""  # FastAPI SERVER URL 설정이 필요할 경우, 해당 변수로 설정

    # LOG
    LEVEL: str = "INFO"
    JSON_LOG: bool = False
    LOGURU_FORMAT: str = (
        "<green>{time:YY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- {process} {thread} {extra[request_id]} <level>{message}</level>"
    )

    # LOG SAVE CONFIG
    SAVE: bool = True
    LOG_SAVE_PATH: str = "./logs"
    ROTATION: str = "00:00"
    RETENTION: str = "10 days"
    COMPRESSION: str = "zip"

    @field_validator("LEVEL")
    def validate_log_level(cls, v):
        if v.upper() not in "CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET".split("|"):
            raise ValueError(f"로그레벨 `LEVEL` 은 'CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET' 만 가능. LEVEL={v}")
        return v

    @field_validator("SERVER_URL")
    def valid_server_url(cls, v):
        server_url_regex = r"^https?:\/\/(www\.)?[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})+(\/[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]*)?$"
        pattern = re.compile(server_url_regex)
        if v:
            if bool(pattern.match(v)):
                return v
            else:
                raise ValueError(f"URL Validation Error (regex {pattern=}), current url={v}")
        else:
            return None

    @computed_field  # type: ignore[misc]
    @property
    def log_level(self) -> Any:  # real return type: numeric value (int)
        return logging.getLevelName(self.LEVEL)

    @computed_field  # type: ignore[misc]
    @property
    def servers(self) -> Union[List[Dict[str, str]], None]:
        if self.SERVER_URL:
            return [{"url": f"{self.SERVER_URL}", "description": f"{self.ENVIRONMENT.capitalize()} Server"}]
        else:
            return None

    @computed_field  # type: ignore[misc]
    @property
    def root_path_in_servers(self) -> bool:
        if self.SERVER_URL:
            return False
        else:
            return True

    # Backend
    BACKEND_CORS_ORIGINS: Annotated[Union[List[AnyUrl], str], BeforeValidator(parse_cors)] = []

    # Service Config
    X_TOKEN: str = "wisenut"

    # DB Config
    SQLITE_FILE_NAME: str = "database.db"

    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "datagokr"

    POSTGRES_VERBOSE: bool = False

    MAXIMUM_INGESTION_LIMIT: int = 200

    # Scoring & Auto-Publish
    AUTO_PUBLISH_THRESHOLD: float = 0.90

    # Snapshot Storage
    SNAPSHOT_STORAGE_PATH: str = "./snapshots"

    # Agent Integration
    AGENT_SERVICE_URL: str = ""  # e.g. "http://langgraph-agent:8090"
    AGENT_REQUEST_TIMEOUT: int = 120  # seconds
    AGENT_ENABLED: bool = False  # feature flag — must be True to enable /regen endpoints


settings = Settings()  # type: ignore
print(settings.model_dump_json())
