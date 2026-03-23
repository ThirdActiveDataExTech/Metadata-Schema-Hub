FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # prevent venv location mismatch
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app/apps/catalog-service

COPY packages/active-metadata /app/packages/active-metadata/
COPY apps/catalog-service/pyproject.toml apps/catalog-service/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --link-mode=copy


# `production` image used for runtime
FROM python:3.11-slim AS production

# Setting home directory, user name, and snapshot path
ENV APP_HOME=/home/wisenut/app \
    SNAPSHOT_STORAGE_PATH=/data/snapshots \
    GROUP_NAME=wisenut \
    APP_USER=wisenut

# Set the working directory
WORKDIR $APP_HOME

# Create user, set permissions, and create snapshot directory (single layer)
RUN groupadd -r $GROUP_NAME && \
    useradd -r -g $GROUP_NAME -d $APP_HOME $APP_USER && \
    chown -R $APP_USER:$GROUP_NAME $APP_HOME && \
    mkdir -p $SNAPSHOT_STORAGE_PATH && \
    chown -R $APP_USER:$GROUP_NAME $SNAPSHOT_STORAGE_PATH

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
COPY apps/catalog-service/pyproject.toml apps/catalog-service/version_info.py* ./
COPY apps/catalog-service/static ./static/
COPY apps/catalog-service/app ./app/

# Expose the port
EXPOSE 8084

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8084"]