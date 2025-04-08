FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    vim \
    jq \
    curl \
    git \
    tzdata \
    net-tools \
    iproute2 \
    htop \
    build-essential \
    strace  \
    apache2-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --link-mode=copy --all-groups


# `development` image is used during development / testing
FROM builder-base AS development

# Setting home directory and user name
ENV APP_HOME=/home/wisenut/app

# Set the working directory
WORKDIR $APP_HOME

# Set environment variables
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy necessary files and directory
COPY --from=builder-base $VIRTUAL_ENV $VIRTUAL_ENV
COPY pyproject.toml uv.lock version_info.py .env ./
COPY ./static ./static/
COPY ./tests ./tests/
COPY ./app ./app/

# Expose the port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/home/wisenut/app", "--reload-exclude", "*.log"]