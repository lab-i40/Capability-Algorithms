"""Write a deterministic text summary from capability check results."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.support.metrics import compute_functional_f1, safe_mean, to_float

_SUMMARY_FILENAME = "summary.txt"
_MAX_REASON_LENGTH = 120


def _format_float(value: float | None, *, precision: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{precision}f}"


def _format_percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00"
    return f"{(numerator / denominator) * 100:.2f}"


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return "None"
    return str(value)


def _trim_reason(reason: Any, max_len: int = _MAX_REASON_LENGTH) -> str:
    if reason is None:
        return "n/a"
    normalized = " ".join(str(reason).split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[: max_len - 3].rstrip()}..."


def write_summary(results: Sequence[Mapping[str, Any]], out_dir: Path) -> Path:
    """Write `summary.txt` in `out_dir` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / _SUMMARY_FILENAME

    ordered_results = sorted(
        (dict(row) for row in results), key=lambda row: str(row.get("test_id", ""))
    )

    total = len(ordered_results)
    passed = sum(1 for row in ordered_results if row.get("status") == "passed")
    failed = sum(1 for row in ordered_results if row.get("status") == "failed")

    model_name = os.getenv("LLM_MODEL", "unknown_model")
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = [
        "=== Capability Check Summary ===",
        f"Model: {model_name}",
        f"Timestamp: {timestamp}",
        f"Total tests executed: {total}",
        f"Passed: {passed} ({_format_percentage(passed, total)}%)",
        f"Failed: {failed} ({_format_percentage(failed, total)}%)",
        "",
        "--- Metricas por suite ---",
    ]

    suites = sorted({str(row.get("suite", "unknown")) for row in ordered_results})
    if not suites:
        lines.append("n/a")
    for suite in suites:
        suite_rows = [row for row in ordered_results if str(row.get("suite")) == suite]
        suite_total = len(suite_rows)
        suite_passed = sum(1 for row in suite_rows if row.get("status") == "passed")
        avg_response_time = safe_mean([to_float(row.get("response_time")) for row in suite_rows])
        avg_total_tokens = safe_mean([to_float(row.get("total_tokens")) for row in suite_rows])
        lines.append(
            f"{suite}: passed={suite_passed}/total={suite_total} "
            f"({_format_percentage(suite_passed, suite_total)}%), "
            f"avg_response_time={_format_float(avg_response_time, precision=4)}, "
            f"avg_total_tokens={_format_float(avg_total_tokens, precision=4)}"
        )

    all_response_time = safe_mean([to_float(row.get("response_time")) for row in ordered_results])
    all_prompt_tokens = safe_mean([to_float(row.get("prompt_tokens")) for row in ordered_results])
    all_completion_tokens = safe_mean(
        [to_float(row.get("completion_tokens")) for row in ordered_results]
    )
    all_total_tokens = safe_mean([to_float(row.get("total_tokens")) for row in ordered_results])
    f1_score = compute_functional_f1(ordered_results)

    lines.extend(
        [
            "",
            "--- Metricas agregadas ---",
            f"F1 (funcionais): {_format_float(f1_score, precision=2)}",
            " / ".join(
                [
                    f"avg_response_time={_format_float(all_response_time, precision=4)}",
                    f"avg_prompt_tokens={_format_float(all_prompt_tokens, precision=4)}",
                    (
                        "avg_completion_tokens="
                        f"{_format_float(all_completion_tokens, precision=4)}"
                    ),
                    f"avg_total_tokens={_format_float(all_total_tokens, precision=4)}",
                ]
            ),
            "",
            "--- Falhas ---",
        ]
    )

    failed_rows = [row for row in ordered_results if row.get("status") == "failed"]
    if not failed_rows:
        lines.append("Nenhuma falha.")
    for row in failed_rows:
        lines.append(
            f"{row.get('test_id')}: expected={_format_scalar(row.get('expected'))} "
            f"actual={_format_scalar(row.get('actual'))} "
            f"reason={_trim_reason(row.get('reason'))}"
        )

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path
