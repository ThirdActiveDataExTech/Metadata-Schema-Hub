FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # prevent venv location mismatch
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app/apps/metadata-ingestion

COPY packages/active-metadata /app/packages/active-metadata/
COPY apps/metadata-ingestion/pyproject.toml apps/metadata-ingestion/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --link-mode=copy


# `production` image used for runtime
FROM python:3.11-slim AS production

# Setting home directory and user name
ENV APP_HOME=/home/wisenut/app \
    GROUP_NAME=wisenut \
    APP_USER=wisenut

# Create a non-root user and group
RUN groupadd -r $GROUP_NAME && useradd -r -g $GROUP_NAME -d $APP_HOME $APP_USER

# Set the working directory
WORKDIR $APP_HOME
RUN chown -R $APP_USER:$GROUP_NAME $APP_HOME

# Set environment variables
ENV TZ=Asia/Seoul \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Switch to the non-root user
USER $APP_USER

# Copy necessary files and directory
COPY --from=builder-base /app/.venv $VIRTUAL_ENV
COPY apps/metadata-ingestion/pyproject.toml apps/metadata-ingestion/version_info.py apps/metadata-ingestion/.env ./
COPY apps/metadata-ingestion/static ./static/
COPY apps/metadata-ingestion/app ./app/

# Expose the port
EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]