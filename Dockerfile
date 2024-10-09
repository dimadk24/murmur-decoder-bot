FROM python:3.12.0-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    # pip
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_DISABLE_PIP_VERSION_CHECK=1\
    # poetry
    POETRY_VERSION=1.7.0 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # Because of the https://chanind.github.io/2021/09/27/cloud-run-home-env-change.html need to set config dir
    # Otherwise during run poetry ignores config set during build
    POETRY_CONFIG_DIR="/home/.config/pypoetry" \
    POETRY_HOME="/usr/local/pypoetry"

RUN python3 -m pip install --user pipx

RUN apt-get -y update && \
    apt-get install ffmpeg -y

RUN pipx install poetry==$POETRY_VERSION

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --only=main --no-root --no-interaction --no-ansi

COPY . /app

ENV PORT="8000"

EXPOSE $PORT

CMD echo $GOOGLE_APPLICATION_CREDENTIALS_JSON | base64 --decode > /app/google-application-credentials.json && poetry run python src/main.py
