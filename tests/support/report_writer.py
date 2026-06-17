"""Escrita dos artefatos de relatório (ver ``docs/plano-refatoracao-testes.md`` §4).

Por caso (``report/TC<n>/TC<n>{P,N}/``):
- ``semantic_matching.md``    — bloco JSON do resultado do Step 1 + ``Reasoning:``.
- ``requirement_matching.md`` — por property set, bloco JSON (``verdict`` +
  ``justification``) + ``Reasoning:``, separados por linha de ``=``.

Agregados (``report/``):
- ``confusion_matrix.csv``  — contagens 2×2 (TP/FN/FP/TN); ``error`` fica de fora.
- ``diagnostic-case.csv``   — uma linha por caso com a situação diagnóstica.

Nada aqui toca ``dataset/`` — só lê o ``CapabilityCheckResult`` em memória e
escreve sob ``report/``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from capability_matching import CapabilityCheckResult

REPORT_ROOT = Path(__file__).resolve().parents[2] / "report"
SEP = "=" * 88


def _case_dir(report_root: Path, test_id: str) -> Path:
    scenario = test_id[:-1]  # "TC11P" -> "TC11"
    d = report_root / scenario / test_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _json_block(obj: Any) -> str:
    return "```json\n" + json.dumps(obj, indent=4, ensure_ascii=False) + "\n```"


def write_case_report(case: dict, result: "CapabilityCheckResult",
                      report_root: Path = REPORT_ROOT) -> Path:
    """Escreve ``semantic_matching.md`` e ``requirement_matching.md`` do caso."""
    out_dir = _case_dir(report_root, case["test_id"])

    sem = result.semantic_response
    semantic_md = (
        _json_block({
            "primary_capability": sem.result.primary_capability,
            "auxiliary_capabilities": sem.result.auxiliary_capabilities,
            "match": sem.result.match,
        })
        + "\n\nReasoning: " + (sem.thinking or "")
        + "\n"
    )
    (out_dir / "semantic_matching.md").write_text(semantic_md, encoding="utf-8")

    if result.requirement_response is None:
        requirement_md = (
            SEP + "\nStep 2 not reached (semantic match was false); no requirement "
            "matching was performed.\n" + SEP + "\n"
        )
    else:
        blocks: list[str] = []
        for ps_id, resp in result.requirement_response.results.items():
            blocks.append(
                SEP
                + f"\nRequirement: {ps_id}\n\n"
                + _json_block({ps_id: {
                    "verdict": resp.result.verdict.value,
                    "justification": resp.result.justification,
                }})
                + "\n\nReasoning: " + (resp.thinking or "")
            )
        requirement_md = "\n".join(blocks) + "\n" + SEP + "\n"
    (out_dir / "requirement_matching.md").write_text(requirement_md, encoding="utf-8")

    return out_dir


def write_confusion_matrix(rows: Sequence[dict], report_root: Path = REPORT_ROOT) -> Path:
    """``confusion_matrix.csv`` 2×2 a partir das linhas diagnósticas.

    Linhas com ``predicted == "error"`` ficam fora da matriz (fora da metodologia).
    """
    tp = fn = fp = tn = 0
    for r in rows:
        gt, pred = r["ground_truth"], r["predicted"]
        if pred not in ("match", "no_match"):
            continue
        if gt == "match":
            tp += pred == "match"
            fn += pred == "no_match"
        else:
            fp += pred == "match"
            tn += pred == "no_match"

    report_root.mkdir(parents=True, exist_ok=True)
    path = report_root / "confusion_matrix.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["", "predicted_match", "predicted_no_match"])
        w.writerow(["actual_match", tp, fn])
        w.writerow(["actual_no_match", fp, tn])
    return path


DIAGNOSTIC_FIELDS = ["test_id", "dimension", "formalism", "ground_truth",
                     "predicted", "situation", "timestamp"]


def write_diagnostic_table(rows: Sequence[dict], report_root: Path = REPORT_ROOT) -> Path:
    """``diagnostic-case.csv`` — uma linha por caso (ordenada por ``test_id``)."""
    report_root.mkdir(parents=True, exist_ok=True)
    path = report_root / "diagnostic-case.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=DIAGNOSTIC_FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["test_id"]):
            w.writerow({k: r.get(k, "") for k in DIAGNOSTIC_FIELDS})
    return path
