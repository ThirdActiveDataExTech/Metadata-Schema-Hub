import pathlib


class Config:
    """DataGoKR config."""
    LANDING_URL_PREFIX = "https://www.data.go.kr/data/"
    LANDING_URL_SUFFIX = {"standard": "standard", "open": "openapi", "file": "file"}
    OPENSCHEMA_URL_PREFIX = "https://www.data.go.kr/catalog/"
    DCAT_URL_PREFIX = "https://www.data.go.kr/dcat/metadata/"
    SAMPLE_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "sample" # TODO: package 구조 변경됨, 확인필요


config = Config()
