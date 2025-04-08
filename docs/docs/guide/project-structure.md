# Project Structure

>
> @tiangolo 가 제공하는 유형(예: api, crud, 모델, 스키마)별로 파일을 구분하는 프로젝트 구조는 범위가 적은 마이크로 서비스 또는 프로젝트에 적합하지만 많은 도메인이 있는 모놀리식에는 맞출 수
> 없다.    
> 더 확장 가능하고 진화할 수 있는 구조는 Netflix의 Dispatch 에서 영감을 얻었다.

- 출처
    - <https://github.com/zhanymkanov/fastapi-best-practices>
    - <https://fastapi.tiangolo.com/tutorial/bigger-applications/>

```
.
├── .gitlab
│   ├── issue_templates     # 이슈 템플릿으로 이슈 생성시 용도별로 선택해서 사용 가능
│   ├── triage     # traige 설정 파일
│   ├── CODEOWNERS      # 코드 소유자 명시 (파일별로 MR에서 그룹 및 사용자를 자동으로 Reviewer로 설정 가능)
│   └── secret-detection-rulset.toml        # GitLab CI의 첫 단계에서 진행하는 Secret Detection에 추가로 설정할 Rule Set
├── app                  # "app" is a Python package
│   ├── api          # (API Endpoints) "routers" is a "Python subpackage" 
│   │   ├── examples    # 라우터에 사용할 예제들 정의
│   │   ├── routers    # 라우터 모음 정의
│   │   ├── __init__.py
│   │   └── api_router.py   # api router endpoint 설정
│   └── exceptions
│   │   ├── __init__.py
│   │   ├── base.py     # 앱에서 발생하는 내부 에러 기본 포맷
│   │   └── service.py     # base.py를 활용하여 앱에서 발생하는 내부 에러들 정의
│   └── schemas          # Pydantic model 설정
│   │   ├── __init__.py
│   │   ├── items.py
│   │   ├── response.py   # 기본 API 응답 포맷
│   │   └── users.py
│   └── src         # (Main Functions) "src" is a "Python subpackage"
│   │   ├── items   # items 관련 로직 소스 코드
│   │   ├── users   # users 관련 로직 소스 코드
│   │   └── __init__.py 
│   └── utils         # 외부 도구 모음
│   │   ├── __init__.py   # users 관련 로직 소스 코드
│   │   └── authenticaiton.py   # 권한 관련 설정
│   ├── __init__.py
│   ├── config.py   # 앱 내부에서 사용할 변수들 설정 (환경변수를 통해서 값을 받아올 수 있음)
│   ├── constants.py   # 상수 설정
│   ├── dependencies.py     # 라우터 관련 의존성 설정
│   ├── handlers.py  # fastapi handlers 정의 (정의 후 main.py에 추가해야함)
│   ├── log.py  # 로그 관련 설정
│   ├── main.py     # main
│   └── version.py  # 버전 관련 정보 생성 및 전달 파일 (앱 실행 전에 해당 파일 수행해서 version_info.py 생성해야함)
├── static  # static files
│   └── guide   # README.md에 가이드 작성을 위한 static 파일들 모음
├── tests   # app directory architecture 에 맞게 unit test 구성
│   └── api
│   │   ├── __init__.py
│   │   ├── test_items.py     # items 관련 API Call 단위테스트
│   │   └── test_users.py     # users 관련 API Call 단위테스트
│   └── src
│   │   ├── __init__.py
│   │   ├── items   # items 관련 로직 단위테스트
│   │   └── users  # users 관련 로직 단위테스트
│   ├── __init__.py
│   ├── check_common_conditions.py      # router unit test 공통 확인 사항, 필요할 경우 추가 공통 테스트 추가해도 됨
│   ├── conftest.py     # pytest conf file
│   └── test_main.py
```

- **api**: API Endpoint. 작성한 API들은 `$HOME/app/main.py`에 router를 추가한다. (ex. `app.include_router(users.router)`)
- **src**: 모듈 메인 기능
- **test**
    - 👉 unit test는 기본적으로 `$HOME/app`의 디렉토리 구조에 맞게 구성한다.
    - unit test는 기능 테스트, API 엔드포인트 테스트, Pydantic 모델 유효성 테스트, 보안 테스트 등 다양한 종류가 있다.
- **Dockerfile**
    - `dev.Dockerfile`: 개발을 위해 필요한 도구 및 라이브러리와 같은 추가적인 종속성을 설치하기 위한 라이브러리들이 설치된 환경
    - `Dockerfile`, `guinicorn.Dockerfile`: 최종 제품을 배포하기 위해 필요한 것들만 포함한 환경
