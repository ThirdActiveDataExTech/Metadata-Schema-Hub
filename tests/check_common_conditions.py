"""단위테스트 공통 체크 사항 함수 모음집"""
from app.config import settings


def check_success_common_conditions(response):
    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert list(response_json.keys()) == ["code", "message", "result", "description"]
    assert response_json["code"] == int(f"{settings.SERVICE_CODE}200")


def check_failed_common_conditions(response, error_type):
    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert list(response_json.keys()) == ["code", "message", "result"]
    assert response_json["code"] == error_type.code
    assert response_json["message"] == error_type.message
    assert response_json["result"] == error_type.result
