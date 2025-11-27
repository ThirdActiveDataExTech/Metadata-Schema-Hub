FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --link-mode=copy


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
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Switch to the non-root user
USER $APP_USER

# Copy necessary files and directory
COPY --from=builder-base $VIRTUAL_ENV $VIRTUAL_ENV
COPY pyproject.toml version_info.py .env ./
COPY ./static ./static/
COPY ./app ./app/

# Expose the port
EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]