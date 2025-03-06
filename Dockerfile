FROM python:3.9-slim

RUN apt-get update && apt-get install -y git

RUN mkdir -p /home/somebody/app
WORKDIR /home/somebody/app

COPY poetry.lock .
COPY pyproject.toml .

ARG PYTHON_REGISTRY=pypi.org/simple
ARG POETRY_VERSION=1.5.0

RUN pip config --user set global.index-url "https://${PYTHON_REGISTRY}" && \
    pip config --user set global.trusted-host "${PYTHON_REGISTRY}" && \
    git config --global --add safe.directory /home/somebody/app

RUN pip install --upgrade pip && pip install poetry==$POETRY_VERSION && \
    pip install poetry-plugin-pypi-mirror && \
    POETRY_PYPI_MIRROR_URL="https://${PYTHON_REGISTRY}" poetry install

COPY . .

RUN poetry run mkdocs build --strict --verbose --site-dir public

FROM nginx:alpine
COPY --from=0 /home/somebody/app/public /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]