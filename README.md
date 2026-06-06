# Capability Algorithms

Reproduction package for the paper **"Large Language Models as a Decision-making Core for Semantic Capability Check in Asset Administration Shell-based Intelligent Manufacturing"**.

This repository contains the source code, test dataset, and prompts used to evaluate LLM-based Capability Check.

**Repository DOI:** [10.5281/zenodo.19687682](https://doi.org/10.5281/zenodo.19687682)

---

## About the Experiment

The Capability Check algorithm determines whether a machine (AAS Provider) can fulfill a service request (AAS Requester) by semantically comparing AAS capability submodels serialized as JSON. It runs in two steps — Step 1 (semantic alignment via the DIN 8580 process taxonomy) and Step 2 (per-property requirement matching) — and returns a `CapabilityCheckResult` whose `matching` boolean is the final verdict.

### Test Matrix

The suite is organized as a **matrix**: 4 abstraction dimensions × 2 formalism degrees = 8 scenarios, each with one positive (`P`, match) and one negative (`N`, no-match) case → **16 cases**, balanced 8 match / 8 no-match. IDs follow `TC<dimension><formalism>` (digit 1 = dimension, digit 2 = formalism):

| | Formal (1) | Informal (2) |
|---|---|---|
| **Granularity (1)** | `TC11` | `TC12` |
| **Process (2)** | `TC21` | `TC22` |
| **Product (3)** | `TC31` | `TC32` |
| **Resource (4)** | `TC41` | `TC42` |

Each `TC<n>` has leaf folders `TC<n>P` and `TC<n>N` under `dataset/`. The dataset (AAS documents + `*_ground_truth.json`) is authored and owned by the maintainer.

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
| `OPENAI_API_KEY` | Yes | Together AI API key. The model and base URL are fixed in `src/` (Together/Qwen), so only the key is injected (D1). |

The suite makes real LLM calls only (no offline/mock path), so `OPENAI_API_KEY` is required to run it (including in CI).

---

## Running the Experiment

Run the full test suite (single pass):

```bash
poetry run pytest
```

Run a subset of the matrix by test id (e.g. one scenario or one dimension):

```bash
poetry run pytest -k "TC11"     # both polarities of Formal × Granularity
poetry run pytest -k "TC11P or TC11N"
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

The suite does not assert pass/fail on the verdict — it executes each case and
records the result, then derives correctness against the ground truth in the
report layer. After execution, artifacts are written under `report/`:

| Path | Description |
|------|-------------|
| `report/TC<n>/TC<n>{P,N}/semantic_matching.md` | Step 1 result (JSON) + reasoning, per case |
| `report/TC<n>/TC<n>{P,N}/requirement_matching.md` | Step 2 verdict + justification (per property set) + reasoning, per case |
| `report/confusion_matrix.csv` | 2×2 counts (TP/FN/FP/TN); class positive = match |
| `report/diagnostic-case.csv` | One row per case: `test_id,dimension,formalism,ground_truth,predicted,situation,timestamp` |

`situation` follows the diagnostic taxonomy of `test_2.tex`:
`correct-clean` / `correct-with-recovery` / `incorrect` (plus `error` for runs
that raised an exception, which are excluded from the confusion matrix). Outcome
accuracy = `correct-clean` + `correct-with-recovery`; path accuracy =
`correct-clean`.
