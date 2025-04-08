## Getting started

### 1. Create Project
>
> 총 3가지 방법이 존재함 (제일 사용하기 편한 방법은 Quick Start 방식 확인)

1. **Create blank project**
    1. GitLab `Create new project` 을 통해 새로운 프로젝트 생성
    2. _Project name, Project description (optional)_ 등을 작성하고 `Create project` 선택
    3. Python FastAPI Template을 Download source code (zip, tar.gz, tar.bz2, tar)를 통해 받아서 Push
2. **Create project using fork**
    1. `Create new Fork` or `Fork`를 통해서 새로운 프로젝트 생성
    2. _Project name, Project description (optional)_ 등을 작성하고 `Fork Project` 선택
    3. 프로젝트 생성 후 Fork 해제    
       Fork를 해제하지 않으면 새로 생성한 프로젝트의 MR이 Python FastAPI Template에 올라오거나 Issue를 통해 Create merge request 불가

### 2. Development Environment Setting

1. 로컬 개발 환경에 `git clone ...`
2. Pycharm 을 열고 `open project ...`
3. Interpreter Setting
   - **uv**
     > requirements: uv 설치 ([uv Getting Started](https://docs.astral.sh/uv/getting-started/installation/#installing-uv) 참고)
     - **`uv sync`**
     - PyCharm으로 진행할 경우
         1. **Add New Interpreter** 선택
         2. **Add Local Interpreter** 선택
         3. **Virtualenv** 선택
         4. Python version에 맞게 환경 설정 (현재는 3.11.11 사용중)
         5. **Install packages from pyproject.toml** 체크
         6. **OK** 선택
         7. 터미널에서 `uv sync` 실행  
         - `uv pip list`로 의존성이 제대로 설치됐는지 확인
   - _Poetry (deprecated)_
     > requirements: Poetry 설치 ([Poetry docs](https://python-poetry.org/docs/#installation) 참고)
     - **`poetry install --no-root`**
     - PyCharm으로 진행할 경우
         1. **Add New Interpreter** 선택
         2. **Add Local Interpreter** 선택
         3. **Poetry Environment** 선택
         4. Python version에 맞게 환경 설정 (현재는 3.9.13 사용중)
         5. **Install packages from pyproject.toml** 체크
            - `UnicodeError` 발생 할 경우, **Settings > Editor > Global Encoding, Project Encoding, Properties Files** 모두 'UTF-8' 로 설정
            - 🐛 해결이 안 될 경우, `Install packages from pyproject.toml` 체크 표시 해제하고 poetry 가상환경 생성한 후 poetry venv 터미널에 `poetry install --no-root`로 직접 의존성 설치
         6. **OK** 선택
         - `poetry show`로 의존성이 제대로 설치됐는지 확인
   - _Virtualenv (deprecated)_
       1. **Add New Interpreter** 선택
       2. **Add Local Interpreter** 선택
       3. **Virtualenv Environment** 선택
       4. 로컬에 설치된 Python 경로를 Base Interpreter 로 설정
       5. `pip install .` (`pyproject.toml`에 작성한 의존성 설치, 아래 **3. Extra Setting** 참고)

## 3. Extra Setting (Optional)

### `config.py` 및 `.env`
>
> 환경 변수로 앱 구동 및 관련 설정 진행
> 환경 변수 우선순위: 환경변수 외부 주입 및 설정 > `.env`에 설정한 값 > `config.py` 디폴트값

- `PORT`: fastapi server port
- `SERVICE_NAME`: 서비스명
- `SERVICE_CODE`: 서비스코드
- `MAJOR_VERSION`: API 메이저 버전
- `STATUS`: API 상태 (개발용: `dev`, 배포용: `prod`)
- 로그 관련 설정: [loguru](https://github.com/Delgan/loguru) 사용하여 로그 세팅
    - `LEVEL`: 로그 레벨 설정
    - `JSON_LOG`: stdout 형식 JSON 출력 여부 결정 (로그 저장도 해당 형식으로 진행됨)
    - `LOGURU_FORMAT`: 로그 포맷팅 설정
      - loguru 라이브러리를 사용해서 환경변수로 설정이 가능하다.
      - 자세한 로그 포맷은 [loguru 공식 문서](https://loguru.readthedocs.io/en/stable/api/logger.html#record)에서 확인 바람
    - `SAVE`: 로그 파일 저장 여부
    - `LOG_SAVE_PATH`: 디렉토리명까지 설정, (default = `YYYY/MM/*.log` 디렉토리 생성)
    - `ROTATION`: 매일 `mm:ss`시에 새로운 로그 파일 생성
    - `RETENTION`: 설정한 시간 이후에 제거 (ex. "1 month 2 weeks", "10h")
    - `COMPRESSION`: 압축 형식 ("gz", "bz2", "xz", "lzma", "tar", "tar.gz", "tar.bz2", "tar.xz", "zip" 등의 형식 지원)
       > `ROTATION`, `RETENTION`, `COMPRESSION`, `LOGURU_FORMAT` 모두 loguru에 있는 파라미터로 자세한 파라미터 정보는 [공식 문서](https://loguru.readthedocs.io/en/stable/api/logger.html#file:~:text=See%20datetime.datetime-,The%20time%20formatting,-To%20use%20your) 확인
- 서비스 관련 설정
    - `X_TOKEN`: API 사용을 위한 토큰값 설정
- 추가로 환경변수로 설정해서 내부에서 사용할 변수가 있다면`config.py`에 추가하고, 환경변수(주입 or `.env`)로 설정하여 사용

### Docker run

- ❗ 도커 빌드 및 실행할 경우, `version.py` 실행 사전 작업 필수 ❗    
    (없을 경우에도 정상작동 되지만 필요한 정보를 볼 수 없음)    
    👉 `version_info.py` 정보 생성 과정
    
    ```python
    service: str = 'Python FastAPI Template'
    version: str = 'v1.2408.08-dev-733a810'
    git_branch: str = 'main'
    git_revision: str = '733a810bff5c29e4f7ffa6f27d2d57991491f895'
    git_short_revision: str = '733a810'
    build_date: str = '2024-08-08 11:25:03'
    ```

- `pyproject.toml` 작성 (참고: [Declaring project metadata](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/))
    - project 메타데이터 작성 (_name_, _version_, ... etc)
    - 의존성 작성: [project] 섹션의 `dependencies`
      - `uv add ${package-name-to-add}`로 추가하면 자동으로 `pyproject.toml` 파일에 의존성이 추가됨
      - [lint, test 등 production 에 포함되지 않는 의존성을 설치하는 방법](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups)
      - [cpu-only, gpu image 등 구성 방법](https://docs.astral.sh/uv/guides/integration/pytorch/)
      - 자세한 사항은 [uv 공식 문서](https://docs.astral.sh/uv/concepts/projects/dependencies/#adding-dependencies) 참고

### 4. Run

- local run
    - uv 가상환경에 진입하지 않았을 경우, 아래 명령어들 중 하나 실행
        - `uv run python $HOME/app/main.py`
        - `uv run uvicorn app.main:app --host 0.0.0.0 --port <port number>`
    - uv 가상환경에 진입할 경우
        1. 가상환경 진입: `source .venv/bin/activate`
        2. 위 명령어에서 `uv run` 제외하고 그대로 실행 (ex. `uvicorn app.main:app --host 0.0.0.0 --port <port number>`)
    - `FileNotFoundError` or `ImportError` 발생시 _Working Directory_ (Working Directory = `$HOME`) 확인하기
    - _<http://localhost:8000/openapi.json>_ or _<http://localhost:8000/docs>_ 로 API 명세 확인 및 테스트
- docker run (dev)    
    `docker build ...` && `docker run -d -p ...` 로 컨테이너 빌드 & 구동
    ```bash
    # 도커 이미지 빌드
    docker build -t python-fastapi-template:dev -f dev.Dockerfile .
    # 컨테이너 구동
    docker run -d --rm --name python-fastapi-template -p 8000:8000 -e X_TOKEN=wisenut python-fastapi-template:dev
    ```
