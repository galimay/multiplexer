#!/bin/bash

pdm run black src/ tests/
pdm run isort src/ tests/
pdm run mypy src/
pdm run ruff check --fix src/ tests/