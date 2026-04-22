# Capability Algorithms

Project for capability validation between AAS submodels, with automated testing support using `pytest`.

## Requirements

- Python 3.11+
- Poetry

## Installation

1. Install project dependencies:

```bash
poetry install --with dev
```

2. Create the environment file:

```bash
cp .env.example .env
```

3. Edit `.env` with the minimum required values:

- `OPENAI_API_KEY`
- `LLM_MODEL`
- `AI_API_BASE_URL`

## Running tests

Run the full test suite:

```bash
poetry run pytest
```

Run only one group:

```bash
poetry run pytest tests/group_1
```

Repeat each test 5 times (`pytest-repeat`):

```bash
poetry run pytest --count=5
```

## Parallel execution (optional)

To use all workers with `-n auto`, install `pytest-xdist`:

```bash
poetry add --group dev pytest-xdist
```

Then run:

```bash
poetry run pytest -n auto
```

Or with repetition:

```bash
poetry run pytest -n auto --count=5
```

## Reports

After execution, results are saved in:

- `reports/<model_name>/results_YYYYMMDD_HHMMSS.json`
- `reports/<model_name>/summary.txt`
- `reports/<model_name>/benchmark_history.csv`
