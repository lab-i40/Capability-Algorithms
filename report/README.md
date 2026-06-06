# Reports

Evaluation artifacts produced when the test suite runs the **Capability Check**
over the 16-case matrix. The test layer never asserts pass/fail on the verdict
(see [`../README.md`](../README.md)); it executes each case, records the
`CapabilityCheckResult`, and the report layer (`tests/support/diagnostics.py` +
`tests/support/report_writer.py`) derives correctness against each case's
`*_ground_truth.json`. Everything here is **generated** — re-running the suite
overwrites it. Nothing in this folder touches `dataset/`.

## Structure

```
report/
├── confusion_matrix.csv          # aggregate: 2×2 outcome counts
├── diagnostic-case.csv           # aggregate: one row per case
└── TC<n>/TC<n>{P,N}/             # per-case reasoning traces
    ├── semantic_matching.md       # Step 1 result + reasoning
    └── requirement_matching.md    # Step 2 result + reasoning
```

`TC<n>` is the scenario (`TC11`…`TC42`); the leaf `TC<n>P` / `TC<n>N` are the
positive (match) and negative (no-match) polarities — the same `TC<dimension><formalism>`
convention as `dataset/` (digit 1 = dimension `1=granularity 2=process 3=product
4=resource`; digit 2 = formalism `1=formal 2=informal`).

## Aggregates (tracked — do not git-ignore)

These two files back the results reported in the paper and are committed on purpose.

### `confusion_matrix.csv`

A 2×2 confusion matrix in absolute counts, with **match** as the positive class.
Rows are the ground truth, columns are the prediction:

```
,predicted_match,predicted_no_match
actual_match,TP,FN
actual_no_match,FP,TN
```

A false positive (declaring an incapable resource capable) is the most costly error
in this manufacturing context. Cases whose run raised an exception (`predicted = error`)
are excluded from the matrix.

### `diagnostic-case.csv`

One row per case (sorted by `test_id`):

| Column | Meaning |
|--------|---------|
| `test_id` | Case id, e.g. `TC11P` |
| `dimension` | `granularity` / `process` / `product` / `resource` |
| `formalism` | `formal` / `informal` |
| `ground_truth` | Expected verdict: `match` / `no_match` |
| `predicted` | Emitted verdict: `match` / `no_match` (or `error`) |
| `situation` | Diagnostic class (below) |
| `timestamp` | ISO-8601 execution time |

The `situation` follows the diagnostic taxonomy in `diagnostics.py`, comparing the
emitted verdict (ŷ) and the reasoning path (τ̂) against ground truth:

| Situation | Condition |
|-----------|-----------|
| `correct-clean` | verdict correct **and** path correct (ŷ == y, τ̂ == τ) |
| `correct-with-recovery` | verdict correct but path differed (ŷ == y, τ̂ ≠ τ) |
| `incorrect` | verdict wrong (ŷ ≠ y) |
| `error` | the run raised an exception (excluded from the confusion matrix) |

Derived metrics: **outcome accuracy** = `correct-clean` + `correct-with-recovery`;
**path accuracy** = `correct-clean`.

## Per-case traces

For each case, under `report/TC<n>/TC<n>{P,N}/`:

- **`semantic_matching.md`** — Step 1 output: a JSON block
  (`primary_capability`, `auxiliary_capabilities`, `match`) followed by the model's
  `Reasoning:` (Chain-of-Thought trace).
- **`requirement_matching.md`** — Step 2 output: one block per required property set
  (its `verdict` + `justification`) plus the `Reasoning:` trace, separated by `=`
  rules. If Step 1 returned no semantic match, this file records that Step 2 was not
  reached.
