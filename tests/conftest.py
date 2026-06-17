"""Orquestração de relatório da suíte (ver ``docs/plano-refatoracao-testes.md`` §4).

Coleta, por caso, ``case``/``loaded``/``result`` do nó; escreve os MDs por caso
em ``pytest_runtest_makereport`` (onde o ``CapabilityCheckResult`` existe — também
no worker, sob xdist) e agrega os 2 CSVs (matriz de confusão + tabela diagnóstica)
em ``pytest_sessionfinish``. A classificação σ_s sai de ``diagnostics`` comparando
o resultado contra o ground truth — **não** do status pass/fail do pytest.

Nada aqui escreve em ``dataset/`` (D6): só lê o resultado em memória e grava sob
``report/``.
"""

from datetime import datetime

import pytest
from dotenv import load_dotenv

from tests.support.diagnostics import classify
from tests.support.report_writer import (
    write_case_report,
    write_confusion_matrix,
    write_diagnostic_table,
)

load_dotenv()


def pytest_sessionstart(session):
    session.results = []


def _resolve_case(item):
    case = getattr(item, "case", None)
    if case is None and hasattr(item, "callspec"):
        case = item.callspec.params.get("case")
    return case if isinstance(case, dict) else None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    case = _resolve_case(item)
    if case is None:
        return

    ground_truth = "match" if case["polarity"] == "P" else "no_match"
    loaded = getattr(item, "loaded", None)
    result = getattr(item, "actual_result", None)

    if result is not None and loaded is not None:
        predicted = "match" if result.matching else "no_match"
        situation = classify(result, loaded.ground_truth)
        try:
            write_case_report(case, result)
        except Exception as exc:  # relatório não deve derrubar a sessão
            print(f"⚠️  Falha ao escrever relatório de {case['test_id']}: {exc}")
    else:
        predicted = "error"
        situation = "error"

    item.session.results.append({
        "test_id": case["test_id"],
        "dimension": case["dimension"],
        "formalism": case["formalism"],
        "ground_truth": ground_truth,
        "predicted": predicted,
        "situation": situation,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    """xdist: agrega no controller as linhas emitidas por cada worker.

    ``optionalhook`` evita erro de validação quando o pytest-xdist não está
    instalado (o hook só é chamado quando o plugin existe).
    """
    _ = error
    worker_rows = node.workeroutput.get("results", [])
    if not hasattr(node.config, "_xdist_results"):
        node.config._xdist_results = []
    node.config._xdist_results.extend(worker_rows)


def pytest_sessionfinish(session):
    try:
        from xdist import is_xdist_worker

        if is_xdist_worker(session):
            session.config.workeroutput["results"] = session.results
            return
    except ImportError:
        pass

    rows = getattr(session.config, "_xdist_results", None)
    if rows is None:
        rows = session.results
    if not rows:  # ex.: --collect-only — não sobrescreve relatórios com vazio
        return

    cm = write_confusion_matrix(rows)
    dt = write_diagnostic_table(rows)
    print(f"\n📊 Matriz de confusão: {cm}")
    print(f"🧭 Tabela diagnóstica: {dt}")
