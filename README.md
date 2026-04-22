# Capability Algorithms

Reproduction package for the paper **"Large Language Models as a Decision-making Core for Semantic Capability Check in Asset Administration Shell-based Intelligent Manufacturing"**.

This repository contains the source code, test dataset, and prompts used to evaluate LLM-based Capability Check across five open-weight models and 454 test cases.

**Repository DOI:** [10.5281/zenodo.19687682](https://doi.org/10.5281/zenodo.19687682)

---

## About the Experiment

The Capability Check algorithm determines whether a machine (AAS Provider) can fulfill a service request (AAS Requester) by semantically comparing two AAS capability submodels serialized as JSON. An LLM acts as the decision-making core, returning a structured JSON response with a `capable` boolean and a textual justification.

### Test Groups

The 454 test cases are organized into four groups, balanced with equal positive (`capable: true`) and negative (`capable: false`) cases:

| Group | Name | Cases |
|-------|------|-------|
| G1 | Semantic Relationship between Capabilities | 102 |
| G2 | Insufficient Inferential Evidence | 110 |
| G3 | Limiting Properties and Parameterization | 106 |
| G4 | Invalid or Inconsistent Data | 136 |

### Models Evaluated

All models are open-weight and were served via [Together AI](https://www.together.ai/):

| Model | Organization | Parameters |
|-------|--------------|------------|
| `openai/gpt-oss-20b` | OpenAI | 20B |
| `openai/gpt-oss-120b` | OpenAI | 120B |
| `Qwen/Qwen3.5-9B` | Alibaba | 9B |
| `Qwen/Qwen3.5-35B-A3B` | Alibaba | 35B |
| `Qwen/Qwen3.5-397B-A17B` | Alibaba | 397B |

### Inference Parameters

Each test case was executed 5 times (`--count=5`) to apply self-consistency. Inference used `temperature=0.7` and `top_p=0.95`.

---

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Installation

1. Install project dependencies from `pyproject.toml`:

```bash
poetry install --with dev
```

2. Create the environment file:

```bash
cp .env.example .env
```

3. Fill in `.env` with the required values (see [Environment Variables](#environment-variables) below).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | API key for the inference provider (Together AI, Groq, OpenAI, etc.) |
| `AI_API_BASE_URL` | Yes | Base URL of the inference server |
| `LLM_MODEL` | Yes | Model identifier string (see examples in `.env.example`) |

Example values for `AI_API_BASE_URL`:

- Together AI: `https://api.together.xyz`
- Groq: `https://api.groq.com/`
- OpenAI: `https://api.openai.com`

---

## Running the Experiment

Run the full test suite (single pass):

```bash
poetry run pytest
```

Run only one group:

```bash
poetry run pytest tests/group_1
```

Repeat each test 5 times to match the paper's methodology (`pytest-repeat`):

```bash
poetry run pytest --count=5
```

### Parallel Execution (optional)

Install `pytest-xdist`:

```bash
poetry add --group dev pytest-xdist
```

Then run with all available workers:

```bash
poetry run pytest -n auto --count=5
```

---

## Reports

After execution, results are saved under `reports/<model_name>/`:

| File | Description |
|------|-------------|
| `results_YYYYMMDD_HHMMSS.json` | Raw per-test results |
| `summary.txt` | Aggregated accuracy and F1 Score |
| `benchmark_history.csv` | Historical run log |
