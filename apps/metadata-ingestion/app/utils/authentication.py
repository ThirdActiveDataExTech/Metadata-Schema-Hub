"""API 사용 권한 관련 로직

현재는 간단한 토큰 스트링 매칭 기반 권한 설정
BUT 추후 API Key 로직을 해당 파일에 적용
필요한 경우, 직접 구현
"""
from app.config import settings
from app.exceptions.service import TokenValidationError


async def token_validation(x_token):
    if x_token != settings.X_TOKEN:
        raise TokenValidationError(x_token)
