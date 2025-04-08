"""
users API는 간단한 예시로 실제 개발시 items API를 참고하길 바람
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.response import APIResponseModel
from app.schemas.users import UserModel, UsersResponseModel
from app.src.users.users import fake_users_db

router = APIRouter()  # APIRouter 변수명은 원하는대로 설정 가능


@router.get("/users", tags=["users"], response_model=APIResponseModel, response_class=JSONResponse)
async def read_users():
    return APIResponseModel(result=UsersResponseModel(users=fake_users_db),
                            description="사용자 가져오기 성공")


@router.get("/users/me", tags=["users"], response_model=APIResponseModel, response_class=JSONResponse)
async def read_user_me():
    return APIResponseModel(result=UserModel(username="fakecurrentuser"), description="사용자 읽기 성공")


@router.get("/users/{username}", tags=["users"], response_model=APIResponseModel, response_class=JSONResponse)
async def read_user(username: str):
    return APIResponseModel(result=UserModel(username=username), description="특정 사용자 읽기 성공")
