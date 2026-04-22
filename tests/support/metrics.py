"""Funções de agregação de métricas dos resultados da suíte."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no", "", "none", "nan"}:
        return False
    return bool(normalized)


def safe_mean(values: Sequence[float | None]) -> float | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def compute_functional_f1(results: Sequence[Mapping[str, Any]]) -> float:
    functional_rows = [row for row in results if row.get("expected") is not None]
    if not functional_rows:
        return 0.0

    tp = 0
    fp = 0
    fn = 0
    for row in functional_rows:
        expected = as_bool(row.get("expected"))
        actual = as_bool(row.get("actual"))
        if expected and actual:
            tp += 1
        elif not expected and actual:
            fp += 1
        elif expected and not actual:
            fn += 1

    denominator = (2 * tp) + fp + fn
    if denominator == 0:
        return 0.0
    return (2 * tp) / denominator


def compute_session_metrics(results: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    perf_rows = [
        row
        for row in results
        if to_float(row.get("response_time")) is not None
        and to_float(row.get("total_tokens")) is not None
    ]

    return {
        "f1_score": compute_functional_f1(results),
        "avg_response_time": safe_mean(
            [to_float(row.get("response_time")) for row in perf_rows]
        ),
        "avg_total_tokens": safe_mean(
            [to_float(row.get("total_tokens")) for row in perf_rows]
        ),
        "avg_prompt_tokens": safe_mean(
            [to_float(row.get("prompt_tokens")) for row in perf_rows]
        ),
        "avg_completion_tokens": safe_mean(
            [to_float(row.get("completion_tokens")) for row in perf_rows]
        ),
    }
