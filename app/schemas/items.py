"""pydantic BaseModel을 기본적으로 활용한다.

- 권장사항
    - Field(title, description, default, ...)를 사용하여 Swagger UI에 디폴트값, 설명, 예시 등을 작성한다.
    - @field_validator(...)를 사용하여 모델의 필드값을 검토하도록 한다.
    - @model_validator(...)를 사용하여 모델 적용 전과 후에 확인할 로직을 작성한다.
    > 자세한 사항은 pydantic 공식 문서 확인
"""

from pydantic import BaseModel, Field, field_validator

from app.exceptions.service import InvalidItemStock
from app.schemas.response import APIResponseModel
from app.version import VERSION


class CreateItemsRequestModel(BaseModel):
    name: str = Field(title="아이템 이름", description="아이템 이름", default="no name")
    status: str
    stock: int

    @field_validator('stock')
    def check_stock(cls, stock):
        if stock < 0:
            raise InvalidItemStock(stock)
        return stock  # return 필수! 작성하지 않으면 null값 return


class Items(BaseModel):
    item_id: str
    name: str


class CreateItemResponse(BaseModel):
    item: CreateItemsRequestModel


class ItemResponseModel(APIResponseModel):
    message: str = Field(default=f"아이템 응답 성공 ({VERSION})")
