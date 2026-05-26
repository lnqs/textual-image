python_versions := "3.12 3.13 3.14"

default: format lint spell types test

format:
    uv sync --locked --no-install-project
    uv run ruff format .

lint:
    uv sync --locked --no-install-project
    uv run ruff check .

spell:
    uv sync --locked --no-install-project
    uv run typos .

types:
    uv sync --locked --extra textual --extra numpy
    uv run mypy .

test:
    uv sync --locked --extra textual --extra numpy
    uv run pytest --cov=textual_image --cov-report=term-missing --color=yes

commits:
    uv sync --locked --no-install-project
    uv run cz check --rev-range origin/main..HEAD

matrix:
    #!/usr/bin/env bash
    set -euo pipefail
    for v in {{python_versions}}; do
        uv python install "$v"
        echo "=== Python ${v} ==="
        UV_PYTHON="${v}" uv sync --locked --extra textual --extra numpy
        UV_PYTHON="${v}" uv run pytest --cov=textual_image --cov-report=term-missing --color=yes
    done
