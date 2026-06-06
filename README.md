# Capability Algorithms

Reproduction package for the paper:

> **Large Language Models as a Decision-Making Core for Semantic Capability Check
> in Asset Administration Shell-Based Intelligent Manufacturing**
>
> Roberto Higino Pereira da Silva, Afonso Henrique Torres Lucas, Daniel Carlos de
> Almeida Mendonça, Vitor Ramon Viana do Carmo (HUB Tecnologia e Inovação, EST,
> Universidade do Estado do Amazonas); Carlos André de Mattos Teixeira, Julio Leite
> Azancort Neto, Romário da Costa Silva, Carlos Renato Lisboa Francês (PPGEE,
> Instituto de Tecnologia, Universidade Federal do Pará).

This repository holds the source code, prompts, test dataset, and evaluation
reports for the LLM-based Capability Check proposed in the paper.

**Repository DOI:** [10.5281/zenodo.19687682](https://doi.org/10.5281/zenodo.19687682)

---

## About the Work

Mass customization and lot-size-one production push manufacturing systems toward
**flexibility as a structural requirement**: instead of building entirely new
products per order, the system must transition efficiently between distinct
production configurations and allocate resources at runtime, without manual
reconfiguration. Realizing this demands describing the *functions* of each asset
in a vendor-neutral, machine-interpretable way — the problem addressed by the
**Capability-Skill-Service (CSS)** model, whose central computational task is
**capability matching**: automatically comparing the capabilities *required* by a
process against those *offered* by a resource.

Two lines have dominated this problem, and the paper frames the work around the
trade-off between them:

- **Ontology-based matching** (OWL / RDF / SPARQL, e.g. MaRCO) offers mature formal
  reasoning by subsumption, but at the cost of fragile interoperability across
  heterogeneous ontologies and scalability limited by manual knowledge engineering.
- **AAS-based description** (the **IDTA 02020 Capability Description submodel**)
  standardizes an interoperable, asset-level representation, but the AAS metamodel
  provides **no native reasoning mechanism** — it gives the substrate, not the
  algorithm.

The paper proposes and evaluates a capability-matching mechanism that operates
**natively over the IDTA 02020 AAS submodel** using a **Large Language Model** as
the decision-making core — recovering semantic reasoning without reintroducing the
dependency on previously agreed ontologies. An OWL/SPARQL knowledge graph serves as
the ontological **baseline**, and both approaches are instantiated over the same two
concrete manufacturing capabilities, **screwing** and **pick-and-place**, to compare
representational expressiveness, matching behavior, and deployment characteristics.

### How the algorithm works

Given a service request (`Requester` AAS) and a machine (`Provider` AAS), the
Capability Check compares AAS capability submodels serialized as JSON and runs in
**two steps**, returning a `CapabilityCheckResult` whose `matching` boolean is the
final verdict:

1. **Step 1 — Semantic matching.** The LLM receives the DIN 8580 process taxonomy
   (serialized in the system prompt) plus the required and offered capability
   containers, and reasons via Chain-of-Thought to align the main process under the
   taxonomy's specificity relation (`⊑`): a more specific offer satisfies a more
   generic requirement (e.g. *Screwing* satisfies *Joining*), but not the reverse.
   If the processes do not align, the check short-circuits to `matching = false`.
2. **Step 2 — Requirement matching.** For the aligned capabilities, each required
   property set is checked against the offered capability; the resource is `capable`
   only if every property set is `satisfied`.

### Test matrix

The suite is organized as a **matrix**: 4 abstraction dimensions × 2 formalism
degrees = 8 scenarios, each with one positive (`P`, match) and one negative (`N`,
no-match) case → **16 cases**, balanced 8 match / 8 no-match. IDs follow
`TC<dimension><formalism>` (digit 1 = dimension, digit 2 = formalism):

|                     | Formal (1) | Informal (2) |
|---------------------|------------|--------------|
| **Granularity (1)** | `TC11`     | `TC12`       |
| **Process (2)**     | `TC21`     | `TC22`       |
| **Product (3)**     | `TC31`     | `TC32`       |
| **Resource (4)**    | `TC41`     | `TC42`       |

Each `TC<n>` has leaf folders `TC<n>P` and `TC<n>N` under `dataset/`.

### Model and inference

The matching pipeline uses **Qwen3.7-Max** (proprietary model from Alibaba Cloud,
announced 20 May 2026), accessed through the **Together AI** API via an
OpenAI-compatible endpoint. It was chosen on operational grounds — explicit
*thinking mode* for Chain-of-Thought, a 1M-token context window, reliable structured
JSON output, and an OpenAI-compatible endpoint — not on aggregate benchmark scores.

Inference prioritizes reasoning stability over answer exploration, in a
**single-execution regime** (no self-consistency):

| Parameter          | Value    |
|--------------------|----------|
| `temperature`      | `0.7`    |
| `top_p`            | `0.95`   |
| `reasoning`        | enabled  |
| `reasoning_effort` | `medium` |
| `stream`           | `true`   |

The model id and base URL are fixed in `src/capability_matching.py`
(`TOGETHER_MODEL`, `TOGETHER_BASE_URL`); only the API key is injected at runtime.

---

## Repository Layout

| Path | What it is |
|------|------------|
| **`src/`** | **The algorithm.** `capability_matching.py` holds the two-step `capability_check()`; `utils.py` parses AAS documents (capability containers, property sets, concept descriptions); `main.py` is a standalone single-case runner. |
| **`src/prompt_templates/`** | **The prompts.** `sys_prompt_s1.md` / `usr_prompt_s1.md` (Step 1, with the DIN 8580 taxonomy injected) and `sys_prompt_s2.md` / `usr_prompt_s2.md` (Step 2). |
| **`src/resources/`** | DIN 8580 taxonomy assets: `DIN8580.owl` and its hierarchical text serialization `din8580_taxonomy.txt`. |
| **`tests/`** | **The test suite.** `test_cases.py` parametrizes the 16-case matrix (no asserts — correctness is derived in the report layer); `support/` holds `matrix.py` (canonical case table), `loader.py`, `runner.py`, `diagnostics.py`, and `report_writer.py`. |
| **`dataset/`** | **The dataset.** `TC<n>/TC<n>{P,N}/` leaf folders with the AAS documents (`*.json`, `*.aasx`) and the per-case `*_ground_truth.json`. Authored and owned by the maintainer. |
| **`report/`** | **Generated evaluation artifacts** — see [`report/README.md`](report/README.md). |

---

## Requirements

- **Python 3.11+** (developed and run on CPython 3.13)
- [**Poetry**](https://python-poetry.org/) for dependency management

### Versions used

| Component        | Version            | Role |
|------------------|--------------------|------|
| Python           | 3.11+ (run on 3.13) | Runtime |
| pytest           | 9.0.3              | Test runner |
| pytest-asyncio   | 1.4.0              | Async test support (`asyncio_mode = auto`) |
| pytest-repeat    | ≥0.9.4, <0.10.0 (dev) | Optional repeated sampling (`--count`) |
| aiohttp          | 3.14.0             | Streaming HTTP client for the Together AI endpoint |
| pydantic         | 2.13.4             | Data models |
| python-dotenv    | 1.2.2              | Loads `.env` |
| openai           | 2.32.0 (pinned in `src/requirements.txt`) | OpenAI-compatible client reference |
| Qwen3.7-Max      | via Together AI    | LLM decision-making core |

---

## Installation

1. Install project dependencies from `pyproject.toml`:

   ```bash
   poetry install --with dev
   ```

2. Create the environment file:

   ```bash
   cp .env.example .env
   ```

3. Fill in `.env` with the required value (see below).

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | **Together AI** API key. The model and base URL are fixed in `src/`, so only the key is injected. |

The suite makes **real LLM calls only** (no offline/mock path), so `OPENAI_API_KEY`
is required to run it (including in CI).

---

## Running the Experiment

Run the full 16-case matrix in a single pass (the paper's regime):

```bash
poetry run pytest
```

Run a subset of the matrix by test id (one scenario or one polarity):

```bash
poetry run pytest -k "TC11"            # both polarities of Formal × Granularity
poetry run pytest -k "TC11P or TC11N"
```

```bash
poetry run pytest
```

## Reports

records the `CapabilityCheckResult`, and derives correctness against the ground
truth in the report layer. After execution, artifacts are written under `report/`.

- `report/confusion_matrix.csv` — 2×2 counts (TP/FN/FP/TN); positive class = match.
- `report/diagnostic-case.csv` — one row per case with its diagnostic situation.

See [`report/README.md`](report/README.md) for the full description and structure.
