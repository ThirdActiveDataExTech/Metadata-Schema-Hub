from typing import Optional, List, Union, Dict
from datetime import datetime

from sqlmodel import Field, SQLModel


class Distribution(SQLModel, table=True):
    """DCAT 3.0의 dcat:Distribution 구현 클래스.

    데이터셋의 특정 형식으로 된 다운로드 가능한 인스턴스를 표현합니다.
    """

    __tablename__: str = "distributions"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    ## dcat properties
    dcat__access_service: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판에 접근하기 위한 데이터 서비스. range: dcat:DataService"
    )
    dcat__access_url: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판에 접근하기 위한 URL. range: rdfs:Resource"
    )
    dcat__byte_size: Optional[int] = Field(
        default=None, nullable=True,
        description="배포판의 크기(바이트 단위). range: rdfs:Literal"
    )
    dcat__compression_format: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 압축 형식. range: dct:MediaType"
    )
    dcat__download_url: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 직접 다운로드 URL. range: rdfs:Resource"
    )
    dcat__media_type: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 미디어 타입(MIME 타입). range: dct:MediaType"
    )
    dcat__package_format: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 패키지 포맷. range: dct:MediaType"
    )
    dcat__spatial_resolution_in_meters: Optional[float] = Field(
        default=None, nullable=True,
        description="배포판의 공간 해상도(미터 단위). range: xsd:decimal"
    )
    dcat__temporal_resolution: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 시간 해상도. range: xsd:duration"
    )

    ## dcterms properties, dcterms == dct
    dct__access_rights: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판에 대한 접근 권한 정보. range: dct:RightsStatement"
    )
    dct__conforms_to: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="배포판이 준수하는 표준 목록. range: dct:Standard"
    )
    dct__description: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판에 대한 설명. range: rdfs:Literal"
    )
    dct__format: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 파일 형식. range: dct:MediaTypeOrExtent"
    )
    dct__issued: Optional[datetime] = Field(
        default=None, nullable=True,
        description="배포판의 공식 발행 날짜. range: rdfs:Literal"
    )
    dct__license: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판 사용에 대한 라이선스 정보. range: dct:LicenseDocument"
    )
    dct__modified: Optional[datetime] = Field(
        default=None, nullable=True,
        description="배포판이 변경된 날짜. range: rdfs:Literal"
    )
    dct__rights: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판에 대한 권리 정보. range: dct:RightsStatement"
    )
    dct__title: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판의 이름. range: rdfs:Literal"
    )

    ## odrl properties
    odrl__has_policy: Optional[str] = Field(
        default=None, nullable=True,
        description="배포판과 관련된 권리 제한사항을 표현하는 ODRL 정책. range: odrl:Policy"
    )

    ## spdx properties
    spdx__checksum: Optional[Dict[str, str]] = Field(
        default=None, nullable=True,
        description="배포판의 무결성을 확인하기 위한 체크섬 정보. range: spdx:Checksum"
    )