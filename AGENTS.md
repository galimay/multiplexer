# Agents
You are an incredible Python engineer, with a clear understanding of performance, user interfaces, design and clean code.

## Technologies

* python
* pdm
* pytest

## Development

Use the virtual environment (.venv) to run python commands.
Use pdm to install packages.
Use pytest to run tests.

## Linters

After implementing changes and running unittests, also execute the following commands to check everything is ok. Activate the virtual environment before running the commands:

pdm run black src/ tests/
pdm run isort src/ tests/
pdm run mypy src/
pdm run ruff check src/ tests/