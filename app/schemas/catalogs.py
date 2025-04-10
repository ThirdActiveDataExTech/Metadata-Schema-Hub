from typing import Optional, List

from sqlmodel import Field

from app.schemas.datasets import Dataset
from app.schemas.resources import Resource


class Catalog(Dataset, Resource, table=True):
    """DCAT 3.0의 dcat:Catalog 구현 클래스.

    데이터셋, 데이터 서비스 및 관련 리소스의 컬렉션을 표현하는 카탈로그.
    """

    __tablename__: str = "catalogs"

    ## dcat properties
    dcat__catalog: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그에 포함된 다른 카탈로그 목록. range: dcat:Catalog"
    )
    dcat__dataset: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그에 등록된 데이터셋 목록. range: dcat:Dataset"
    )
    dcat__record: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그의 카탈로그 레코드 목록. range: dcat:CatalogRecord"
    )
    dcat__resource: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그가 포함하는 리소스 목록. range: dcat:Resource"
    )
    dcat__service: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그에 등록된 데이터 서비스 목록. range: dcat:DataService"
    )
    # 자주 사용되지 않음
    dcat__theme_taxonomy: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="이 카탈로그에서 사용하는 주제 분류체계. range: skos:ConceptScheme"
    )

    ## foaf properties
    foaf__home_page: Optional[str] = Field(
        default=None, nullable=True,
        description="이 카탈로그의 홈페이지 URL. range: foaf:Document"
    )
