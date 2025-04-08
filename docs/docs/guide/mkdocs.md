# Mkdocs

> 사용자는 해당 프로젝트에 포함된 mkdocs CI/CD 파이프라인을 이용하여 Markdown으로 작성한 문서를 빌드 및 배포할 수 있습니다.    
> 또한 해당 프로젝트의 API Spec을 명시하는 페이지를 자동으로 생성할 수 있습니다.

## Getting started

1. `docs/mkdocs.yml` 파일 작성 - 문서 구조와 필요한 플러그인을 설정합니다.
2. 작성한 `mkdocs.yml` 파일에 맞춰 `docs/` 위치에 문서(.md) 작성 및 필요한 이미지를 생성합니다.
3. `version.txt`에 현재 문서의 버전 (최신 버전)을 작성합니다. (ex 0.1, 0.0.2 등 자유롭게)
4. 변경사항을 push 합니다.
5. CI 파이프라인이 동작하면서 작성한 문서를 deploy-pages에 배포합니다.
    - 클러스터에 해당 mkdocs 문서를 배포하기 전, 생성된 mkdocs문서를 확인할 수 있습니다. (`Settings - Deploy - pages`)
6. Pipelines에서 manual job인 `build` 를 수동으로 실행시켜 해당 문서 이미지를 빌드합니다.
7. 프로젝트 GitLab Container Registry에 등록된 mkdocs 이미지를 최종 배포합니다.
8. GitLab Container Registry 이미지를 가져와서 컨테이너를 실행합니다.
   ```bash
   # GitLab 로그인이 되어있다는 가정하에
   docker pull ${mkdocs container registry image}
   docker run --name ${container_name} --rm -it -p ${your port}:8080 ${image}/mkdocs:${tag}
   ```

## Warning

- `.dockerignore` 작성
    - Application Project의 `.dockerignore` 파일에 다음 경로를 포함해선 안됩니다.
    - `/docs `, `.git`

## Mkdocs CI/CD Pipeline

``` mermaid
graph TD
    B{'/app' 변경사항?} -->|Yes| C[job:get_api_spec - api.json];
    B --> |No| N1{'/docs' 변경사항?};
    N1 --> |Yes| H[job: test_mkdocs]
    N1 --> |No| K(end pipeline)
    C --> D[job:test_artifact - lint api.json];
    D --> E[job:render_html - docs.html];
    E --> F{'docs.html' 변경사항?};
    F --> |Yes| G[job:deploy_api - push docs.html to project];
    F --> |No| N1;
    G --> H
    H --> I[job: deploy_mkdocs - GitLab Pages 배포]
    I --> |Manual| J[job: build_mkdocs - docker build & container registry push]
    J --> K
```

- GitLab Pages는 `/docs` 에 변경사항이 있을 경우, 브랜치와 상관없이 무조건 푸시합니다. (문서 배포 확인용)
- ⚠ _build_and_push_mkdocs_ job 은 직접 실행해야됩니다. (manual)

## Mkdocstring

> mkdocstrings는 Python 코드의 docstring을 자동으로 Markdown 형식으로 변환하여 API 문서화를 도와주는 MkDocs 플러그인입니다. 이를 통해 코드의 함수, 클래스, 메서드 등의
> 설명을 쉽게 웹 문서로 변환할 수 있습니다.    
> 현재 GitLab CI/CD 파이프라인에 포함되어 있어 mkdocs 문서내에서 자동으로 확인 가능합니다.

- **자동 문서화**: Python 파일 내의 docstring을 자동으로 분석하여 문서화합니다.
- **다양한 docstring 스타일 지원**: Google, NumPy, reStructuredText 스타일을 지원합니다.
- **Markdown 호환**: MkDocs와 호환되어 Markdown 파일 내에서 바로 Python 코드를 문서화할 수 있습니다.
- **소스 코드 보기 옵션**: 소스 코드와 docstring을 함께 볼 수 있는 옵션을 제공합니다.
- **디렉토리 경로 설정 가능**: 여러 Python 파일을 한 번에 문서화할 수 있도록 경로를 지정할 수 있습니다.

### 사용법

1. 기본 설정
    - `docs/mkdocs.yml` 파일에서 플러그인 설정
2. Mkardown 파일에서 사용
    - 각 Python 파일을 문서화하려면, `docs/docs/docstring.md`에서 `::: <module>` 문법을 사용하여 Python 모듈을 호출합니다.

### 참고

- <https://mkdocstrings.github.io/>
- <https://github.com/mkdocstrings/mkdocstrings>
- <https://mkdocstrings.github.io/python/>