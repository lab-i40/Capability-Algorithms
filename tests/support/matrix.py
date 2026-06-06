"""Tabela canônica dos 16 casos da matriz de avaliação.

Convenção de IDs do dataset (ver ``docs/plano-refatoracao-testes.md`` §3.4):
``TC<dimensão><formalismo>`` — **dígito 1 = dimensão**, **dígito 2 = formalismo**.

    dimensão:   1=granularity  2=process  3=product  4=resource
    formalismo: 1=formal       2=informal

Cada cenário ``TC<n>`` tem um caso positivo ``TC<n>P`` (match) e um negativo
``TC<n>N`` (no-match) → 16 casos. Este módulo é o **contrato** entre os testes /
relatórios e o dataset: ele apenas referencia os caminhos das pastas-folha
(``dataset/TC<n>/TC<n>{P,N}/``); **não lê nem escreve o conteúdo do dataset**.
"""

from __future__ import annotations

from pathlib import Path

DATASET_ROOT = Path(__file__).resolve().parents[2] / "dataset"

DIMENSIONS = {"1": "granularity", "2": "process", "3": "product", "4": "resource"}
FORMALISMS = {"1": "formal", "2": "informal"}
POLARITIES = ("P", "N")


def _build_cases() -> list[dict]:
    cases: list[dict] = []
    for dim_digit, dimension in DIMENSIONS.items():
        for form_digit, formalism in FORMALISMS.items():
            scenario = f"TC{dim_digit}{form_digit}"
            for polarity in POLARITIES:
                test_id = f"{scenario}{polarity}"
                cases.append({
                    "test_id": test_id,
                    "scenario": scenario,
                    "dir": DATASET_ROOT / scenario / test_id,
                    "dimension": dimension,
                    "formalism": formalism,
                    "polarity": polarity,
                })
    return cases


ALL_CASES: list[dict] = _build_cases()

CASES_BY_ID: dict[str, dict] = {c["test_id"]: c for c in ALL_CASES}


def case_by_id(test_id: str) -> dict:
    """Retorna o descritor do caso pelo ``test_id`` (ex.: ``"TC11P"``)."""
    return CASES_BY_ID[test_id]
