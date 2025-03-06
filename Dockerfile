FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /install

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip poetry \
    && poetry install --no-root

FROM builder AS docs

WORKDIR /docs
COPY docs ./docs
COPY mkdocs.yml .
COPY pyproject.toml poetry.lock ./

RUN poetry run mkdocs build --strict --verbose --site-dir public

FROM nginx:alpine

COPY --from=docs /docs/public /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

