from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class Resource(SQLModel, table=True):
    """DCAT 3.0 의 dcat:Resource 구현 클래스.

    DCAT (Data Catalog Vocabulary) 3.0 표준의 Resource 추상 클래스를 SQLModel로 구현합니다.

    Notes:
        field 별 description 의 range 는 타입을 의미함

        DB 매핑 시 field 의 `__` 는 `:` 로 변환, camelCase 로 변환 되어야 함.

        예시: `dcat__contact_point` == `dcat:contactPoint`.

        해당 클래스는 직접 사용할 수 없음, 이 클래스를 상속 받은 클래스만 사용 가능함.
    """

    __tablename__: str = "resources"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # TODO: range validation

    ## adms properties
    adms__status: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스의 워크플로우 상태를 나타냄. range: skos:Concept"
    )
    adms__version_notes: Optional[str] = Field(
        default=None, nullable=True,
        description="현재 버전의 변경사항에 대한 설명. range: rdfs:Literal"
    )

    ## dcat properties
    dcat__contact_point: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스에 대한 문의를 위한 연락처 정보. range: vcard:Kind"
    )
    dcat__first: Optional[str] = Field(
        default=None, nullable=True,
        description="순서가 있는 아이템 시리즈의 첫 번째 아이템. range: rdfs:Resource"
    )
    dcat__has_version: Optional[str] = Field(
        default=None, nullable=True,
        description="현재 리소스의 변형, 버전 또는 판을 참조하는 URI. range: dcat:Resource"
    )
    dcat__keyword: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="리소스를 설명하는 키워드나 태그. range: rdfs:Literal"
    )
    dcat__landing_page: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스에 접근하기 위한 웹 페이지 URL. range: foaf:Document"
    )
    dcat__last: Optional[str] = Field(
        default=None, nullable=True,
        description="순서가 있는 아이템 시리즈의 마지막 아이템. range: rdfs:Resource"
    )
    dcat__prev: Optional[str] = Field(
        default=None, nullable=True,
        description="순서가 있는 아이템 시리즈의 이전 아이템. range: rdfs:Resource"
    )
    dcat__previous_version: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스의 이전 버전을 참조하는 URI. range: dcat:Resource"
    )
    dcat__qualified_relation: Optional[str] = Field(
        default=None, nullable=True,
        description="다른 리소스와의 관계를 설명하는 링크. range: dcat:Relationship"
    )
    dcat__theme: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="리소스의 주요 카테고리나 주제. range: skos:Concept"
    )
    dcat__version: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스의 버전 정보. range: rdfs:Literal"
    )

    ## dcterms properties, dcterms == dct
    dct__access_rights: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스 접근 권한 정보 또는 보안 상태 표시. range: dcterms:RightsStatement"
    )
    dct__conforms_to: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스가 준수하는 확립된 표준. range: dcterms:Standard"
    )
    dct__creator: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스 생성에 주요 책임이 있는 엔티티. range: foaf:Agent"
    )
    dct__description: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스에 대한 설명. range: rdfs:Literal"
    )
    dct__has_part: Optional[str] = Field(
        default=None, nullable=True,
        description="현재 리소스에 물리적/논리적으로 포함된 관련 리소스. range: rdfs:Resource"
    )
    dct__identifiers: Optional[str] = Field(
        default=None, nullable=True,
        description="특정 컨텍스트 내에서 리소스에 대한 명확한 참조. range: rdfs:Literal"
    )
    dct__is_referenced_by: Optional[str] = Field(
        default=None, nullable=True,
        description="현재 리소스를 참조하거나 인용하는 관련 리소스. range: rdfs:Resource"
    )
    dct__issued: Optional[datetime] = Field(
        default=None, nullable=True,
        description="리소스의 공식 발행 날짜. range: rdfs:Literal"
    )
    dct__language: Optional[List[str]] = Field(
        default=None, nullable=True,
        description="리소스의 언어. range: dcterms:LinguisticSystem"
    )
    dct__license: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스 사용에 대한 공식 허가를 제공하는 법적 문서. range: dcterms:LicenseDocument"
    )
    dct__modified: Optional[datetime] = Field(
        default=None, nullable=True,
        description="리소스가 변경된 날짜. range: rdfs:Literal"
    )
    dct__publisher: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스를 이용 가능하게 한 책임 엔티티. range: foaf:Agent"
    )
    dct__relation: Optional[str] = Field(
        default=None, nullable=True,
        description="관련 리소스. range: rdfs:Resource"
    )
    dct__replaces: Optional[str] = Field(
        default=None, nullable=True,
        description="현재 리소스에 의해 대체되는 관련 리소스. range: rdfs:Resource"
    )
    dct__rights: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스에 대해 보유한 권리 정보. range: dcterms:RightsStatement"
    )
    dct__title: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스에 주어진 이름. range: rdfs:Literal"
    )
    dct__type: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스의 성격이나 장르. range: rdfs:Class"
    )

    ## odrl properties
    odrl__has_policy: Optional[str] = Field(
        default=None, nullable=True,
        description="리소스와 관련된 권리와 제한사항을 표현하는 ODRL 정책 링크. range: odrl:Policy"
    )

    ## prov properties
    prov__qualified_attribution: Optional[str] = Field(
        default=None, nullable=True,
        description="활동에서 특정 역할을 맡은 에이전트의 귀속 정보. range: prov:Attribution"
    )
