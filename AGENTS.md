# Agents
You are an incredible Python engineer, with a clear understanding of performance, user interfaces, design and clean code.

## Technologies

* python
* pdm
* pytest

## Development

* Use the virtual environment (.venv) to run python commands.

´´´
source .venv/Scripts/activate && pdm install
´´´

* Use pdm to install packages.
* Use pytest to run tests.

## Linters

After implementing changes and running unittests, also execute the following commands to check everything is ok. Activate the virtual environment before running the commands:

´´´
source .venv/Scripts/activate && pdm run black src/ tests/
source .venv/Scripts/activate && pdm run isort src/ tests/
source .venv/Scripts/activate && pdm run mypy src/
source .venv/Scripts/activate && pdm run ruff check src/ tests/
´´´