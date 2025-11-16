import logging
from typing import Callable

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.exceptions.base import ApplicationError


class ExceptionHandlingRoute(APIRoute):
    """비-HTTPException을 HTTPException으로 변환하는 커스텀 APIRoute.

    ServerErrorMiddleware의 re-raise 동작을 방지하여 "Exception in ASGI application"
    로그를 제거하면서도 적절한 예외 처리를 유지합니다.

    Background:
        FastAPI/Starlette는 예외를 두 가지 경로로 처리합니다:

        1. HTTPException 계열 (HTTPException 및 서브클래스):
           - ExceptionMiddleware에서 처리
           - exception handler 실행 후 re-raise 없음
           - "Exception in ASGI application" 로그 없음

        2. 그 외 모든 예외 (OperationalError, ValueError 등):
           - ServerErrorMiddleware에서 처리
           - exception handler 실행 후 예외를 다시 re-raise (설계상 동작)
           - Uvicorn이 re-raise된 예외를 잡아서 "Exception in ASGI application" 로그 출력

        이는 FastAPI/Starlette의 확인된 구조적 한계입니다.

    Solution:
        모든 비-HTTPException을 HTTPException으로 변환하여 첫 번째 경로 사용:
        1. Route handler 실행 중 모든 비-HTTPException을 가로챔
        2. HTTPException으로 변환하여 ExceptionMiddleware 경로로 라우팅
        3. re-raise 동작을 방지하여 불필요한 로그 제거
        4. 기존 exception handler들이 HTTPException에 대해서도 계속 동작

    Alternatives:
        - uvicorn.error 로거 비활성화: logging.getLogger("uvicorn.error").propagate = False
        - 서비스 레이어에서 직접 HTTPException으로 변환

    Note:
        실제 unhandled 버그도 HTTPException으로 변환되므로 디버깅 시 주의 필요.
        원본 예외 정보는 'from exc' 체이닝을 통해 traceback에 보존됩니다.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except (HTTPException, StarletteHTTPException):
                # HTTPException 계열은 그대로 re-raise
                # 기존 http_exception_handler가 처리
                raise
            except Exception as exc:
                # 모든 비-HTTPException을 HTTPException으로 변환
                # 이후 흐름은 HTTPException 전용 exception handler가 처리
                # detail에 원본 예외 정보를 담음
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": 100500,
                        "message": f"Internal Server Error: {type(exc).__name__}",
                        "result": {
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                        },
                    },
                ) from exc

        return custom_route_handler


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logging.error(f"{request.client} {request.method} {request.url} → {repr(exc)}")
    status_code = int(f"{settings.SERVICE_CODE}{exc.status_code}")
    if exc.status_code == 404:
        return JSONResponse(
            status_code=200,
            content=ApplicationError(
                code=status_code,
                message="Invalid URL. see api-doc `/docs` or `/openapi.json`",
                result={"detail": exc.detail},
            ).to_dict(),
        )
    return JSONResponse(
        status_code=200,
        content=ApplicationError(code=status_code, message=exc.detail, result={"headers": exc.headers}).to_dict(),
    )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"{request.client} {request.method} {request.url} → {repr(exc)}")
    return JSONResponse(
        status_code=200,
        content=ApplicationError(
            code=int(f"{settings.SERVICE_CODE}{status.HTTP_422_UNPROCESSABLE_ENTITY}"),
            message=f"Invalid Request: {exc.errors()[0]['msg']} (type: {exc.errors()[0]['type']}), "
            f"Check {(exc.errors()[0]['loc'])}",
            result=exc.body,
        ).to_dict(),
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    logging.error(f"{request.client} {request.method} {request.url} → {repr(exc)}")
    return JSONResponse(
        status_code=200,
        content=ApplicationError(
            code=int(f"{settings.SERVICE_CODE}{status.HTTP_422_UNPROCESSABLE_ENTITY}"),
            message="Pydantic Model ValidationError",
            result=exc.errors(),
        ).to_dict(),
    )


async def application_error_handler(request: Request, exc: ApplicationError):
    logging.error(f"{request.client} {request.method} {request.url} → {repr(exc)}")
    return JSONResponse(
        status_code=200, content=ApplicationError(code=exc.code, result=exc.result, message=exc.message).to_dict()
    )
