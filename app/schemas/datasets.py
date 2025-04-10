from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from sqlmodel import Field

from app.schemas.resources import Resource


class Dataset(Resource, table=True):
    """DCAT 3.0의 dcat:Dataset 구현 클래스.

    데이터셋 리소스에 대한 메타데이터를 표현합니다.
    """

    __tablename__: str = "datasets"

    ## dcat properties
    dcat__distribution: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="데이터셋의 배포 형식 목록. 다운로드나 API 등 데이터에 접근할 수 있는 방법들. range: dcat:Distribution"
    )
    dcat__in_series: Optional[str] = Field(
        default=None, nullable=True,
        description="이 데이터셋이 속한 시리즈. range: dcat:DatasetSeries"
    )
    # 자주 사용되지 않음
    dcat__spatial_resolution_in_meters: Optional[float] = Field(
        default=None, nullable=True,
        description="데이터셋의 공간 해상도(미터 단위). range: xsd:decimal"
    )
    # 자주 사용되지 않음
    dcat__temporal_resolution_in_seconds: Optional[float] = Field(
        default=None, nullable=True,
        description="데이터셋의 시간 해상도(초 단위). range: xsd:decimal"
    )

    ## dcterms properties, dcterms == dct
    # 자주 사용되지 않음
    dct__accrual_periodicity: Optional[str] = Field(
        default=None, nullable=True,
        description="데이터셋이 갱신되는 주기. range: dcterms:Frequency"
    )
    dct__spatial: Optional[Dict[str, Any]] = Field(
        default=None, nullable=True,
        description="데이터셋이 다루는 지리적 영역. range: dcterms:Location"
    )
    # 자주 사용되지 않음
    dct__temporal: Optional[Tuple[datetime, datetime]] = Field(
        default=None, nullable=True,
        description="데이터셋이 다루는 시간 범위(시작일, 종료일). range: dcterms:PeriodOfTime"
    )

    ## prov properties
    # 자주 사용되지 않음
    prov__was_generated_by: Optional[str] = Field(
        default=None, nullable=True,
        description="데이터셋을 생성한 활동이나 프로세스. range: prov:Activity"
    )
