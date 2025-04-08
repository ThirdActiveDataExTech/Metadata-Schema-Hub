"""conftest.py: fixture 와 hook 이라는 기능을 이용해 모든 테스트파일에 특정 기능 혹은 특정 값을 공유/적용할 수 있음

conftest.py 라는 이름의 파일을 pytest가 자동으로 인식을 해주기 때문에, 실제 fixture기능을 호출해야하는 테스트파일들에서, 별도의 import 문을 기재하지 않아도 자동으로 사용할 수 있음
또한 테스트파일들이 여러 중첩된 디렉토리 하위에 존재하고 있다면 해당 디렉토리들에 각각의 conftest.py를 작성하여 해당 디렉토리에 대한 scope로만 동작하는 fixture, hook들을 구성해줄 수도 있고, 동일한 이름의 fixture에 대해 over-ride도 가능함

[각 단위테스트 수행시간 측정]
해당 함수의 대체재로 간단하게 `pytest --durations=0` 으로 단위테스트 수행 시간을 측정할 수 있지만 정확한 수행 시간 파악 불가
사용하지 않을 경우, 삭제 가능

[예시]
Test durations:
+-------------------+-----------------------+
|       Test        |  Duration (seconds)   |
+-------------------+-----------------------+
| test_update_admin | 0.011404037475585938  |
|  test_read_items  | 0.0048139095306396484 |
|  test_read_item   | 0.005265951156616211  |
| test_update_item  | 0.004145145416259766  |
| test_create_item  | 0.004044294357299805  |
|  test_read_users  | 0.003604888916015625  |
| test_read_user_me | 0.0031158924102783203 |
|  test_read_user   | 0.003624439239501953  |
|     test_root     | 0.007190227508544922  |
|    test_health    | 0.003683328628540039  |
+-------------------+-----------------------+
"""

from time import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from sqlmodel.pool import StaticPool
from tabulate import tabulate

from app.dependencies import get_session
from app.main import app

test_durations = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    item.start_time = time()
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_teardown(item, nextitem):
    outcome = yield
    duration = time() - item.start_time
    test_durations.append((item.name, duration))


@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if test_durations:
        headers = ["Test", "Duration (seconds)"]
        table = tabulate(test_durations, headers, tablefmt="pretty")
        terminalreporter.write("\nTest durations:\n")
        terminalreporter.write(table)
        terminalreporter.write("\n")


@pytest.fixture(scope="function")
def engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
def session(engine):
    """2. 테스트용 세션 + DB 초기화"""
    SQLModel.metadata.drop_all(engine)  # 테스트 시작 전 테이블 초기화
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)  # 테스트 종료 후 정리


@pytest.fixture(scope="function")
def client(session):
    """✅ 3. FastAPI 테스트 클라이언트 + session 오버라이드"""

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def common_variable():
    """단위테스트 세션 전체에서 사용할 변수 설정"""
    return {"key": "value"}


@pytest.fixture(scope="session")
def create_item_example():
    return {"name": "apple", "status": "in stock", "stock": 10}


@pytest.fixture(scope="session")
def create_item_lower_than_zero_exception_item_example():
    return {"name": "apple", "status": "in stock", "stock": -1}
