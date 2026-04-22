import csv
import json
import time
from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

from tests.support.metrics import compute_session_metrics
from tests.support.report_paths import current_report_dir
from tests.support.summary_writer import write_summary

load_dotenv()


def _derive_suite(item) -> str:
    file_path = Path(str(item.fspath))
    parent_name = file_path.parent.name
    if parent_name.startswith("group_"):
        return parent_name

    stem = file_path.stem
    if stem.startswith("test_"):
        return stem.replace("test_", "", 1)
    return stem


def pytest_sessionstart(session):
    """
    Hook executado no início da sessão de testes. Inicializa a lista de resultados.
    """
    session.results = []


def pytest_testnodedown(node, error):
    """
    Hook xdist: chamado no controller quando um worker finaliza.
    Coleta os resultados do worker via workeroutput.
    """
    _ = error
    worker_results = node.workeroutput.get("results", [])
    if not hasattr(node.config, "_xdist_results"):
        node.config._xdist_results = []
    node.config._xdist_results.extend(worker_results)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook para acessar o resultado de cada teste individual.
    Esta versão unificada captura dados de todos os tipos de teste.
    """
    _ = call
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if hasattr(item, "callspec"):
            case = item.callspec.params.get("case")
            if isinstance(case, dict):
                test_id = case.get("test_id", item.callspec.id)
                expected = case.get("expected_result")
            else:
                test_id = item.callspec.id
                expected = None
        else:
            test_id = item.name
            expected = None

        actual_result_obj = getattr(item, "actual_result_obj", None)
        requester_after_change = getattr(item, "requester_after_change", None)
        provider_after_change = getattr(item, "provider_after_change", None)

        actual_value = None
        reason_value = None
        prompt_value = None
        response_time = getattr(item, "response_time", None)
        total_tokens = None
        prompt_tokens = None
        completion_tokens = None
        did_get_valid_completion = None
        observed_throughput = None
        raw_model_response = None
        output_reasoning = None

        if isinstance(actual_result_obj, dict):
            actual_value = actual_result_obj.get("capable")
            reason_value = actual_result_obj.get("reason")
            prompt_tokens = actual_result_obj.get("prompt_tokens")
            completion_tokens = actual_result_obj.get("completion_tokens")
            raw_model_response = actual_result_obj.get("raw_output")
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

        item.session.results.append(
            {
                "test_id": test_id,
                "suite": _derive_suite(item),
                "expected": expected,
                "actual": actual_value,
                "duration": report.duration,
                "status": "passed" if not report.failed else "failed",
                "requester_after_change": requester_after_change,
                "provider_after_change": provider_after_change,
                "prompt": prompt_value,
                "reason": reason_value,
                "did_get_valid_completion": did_get_valid_completion,
                "response_time": response_time,
                "observed_throughput": observed_throughput,
                "raw_model_response": raw_model_response,
                "output_reasoning": output_reasoning,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }
        )


def pytest_sessionfinish(session):
    """
    Hook que é chamado no final da sessão.
    Salva os resultados detalhados e atualiza o log histórico.
    """
    try:
        from xdist import is_xdist_worker

        if is_xdist_worker(session):
            session.config.workeroutput["results"] = session.results
            return
    except ImportError:
        pass

    all_results = getattr(session.config, "_xdist_results", None)
    if all_results is None:
        all_results = session.results

    reports_dir = current_report_dir()
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_results_path = reports_dir / f"results_{timestamp_str}.json"

    def default_converter(obj):
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(
            f"Object of type {obj.__class__.__name__} is not JSON serializable"
        )

    with current_results_path.open("w", encoding="utf-8") as file_obj:
        json.dump(
            all_results,
            file_obj,
            indent=4,
            default=default_converter,
            ensure_ascii=False,
        )
    print(f"\n✅ Relatório detalhado salvo em: {current_results_path}")

    summary_path = write_summary(all_results, reports_dir)
    print(f"📝 Resumo textual salvo em: {summary_path}")

    history_path = reports_dir / "benchmark_history.csv"
    session_metrics = compute_session_metrics(all_results)

    if (
        all_results
        and session_metrics.get("avg_response_time") is not None
        and session_metrics.get("avg_total_tokens") is not None
    ):
        summary = {
            "timestamp": timestamp_str,
            **session_metrics,
        }

        fieldnames = [
            "timestamp",
            "f1_score",
            "avg_response_time",
            "avg_total_tokens",
            "avg_prompt_tokens",
            "avg_completion_tokens",
        ]
        write_header = not history_path.exists()
        with history_path.open("a", encoding="utf-8", newline="") as history_file:
            writer = csv.DictWriter(history_file, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {key: ("" if value is None else value) for key, value in summary.items()}
            )
        print(f"📈 Log histórico de benchmarks atualizado em: {history_path}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    delay_marker = item.get_closest_marker("delay")
    if delay_marker:
        time.sleep(delay_marker.args[0])
    start = time.perf_counter()
    try:
        yield
    finally:
        item.response_time = time.perf_counter() - start
