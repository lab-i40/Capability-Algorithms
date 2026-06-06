"""Carrega um caso de teste (AAS + ground truth) a partir de uma pasta-folha.

Espelha o padrão de ``src/main.py``: documentos AAS completos são reduzidos a
*capability containers* via :func:`utils.get_capability_containers` e as concept
descriptions de provedor e requisitante são unidas via
:func:`utils.merge_concept_descriptions`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils import get_capability_containers, merge_concept_descriptions


@dataclass
class Case:
    """Um caso `TC<n>{P,N}` pronto para :func:`tests.support.runner.run_check`."""

    test_id: str
    tc_dir: Path
    required_container: dict[str, Any]
    provided_containers: list[dict[str, Any]]
    concept_descriptions: list[dict[str, Any]]
    ground_truth: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find_one(tc_dir: Path, pattern: str) -> Path:
    """Retorna o único ``.json`` que casa com ``pattern`` dentro de ``tc_dir``."""
    matches = sorted(tc_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern!r} in {tc_dir}")
    if len(matches) > 1:
        raise ValueError(
            f"Multiple files matching {pattern!r} in {tc_dir}: "
            f"{[m.name for m in matches]}"
        )
    return matches[0]


def _capability_containers(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return get_capability_containers(doc["assetAdministrationShells"][0], doc["submodels"])


def load_case(tc_dir: str | Path) -> Case:
    """Carrega o caso na pasta-folha ``tc_dir`` (ex.: ``dataset/TC11/TC11P``).

    A pasta deve conter exatamente um documento AAS de requisitante
    (``*Requester*.json``), um de provedor (``*Provider*.json``) e um ground
    truth (``*ground_truth*.json``). O *required container* é o de índice 0 do
    requisitante, alinhado a ``src/main.py``.
    """
    tc_dir = Path(tc_dir)

    requester_doc = _load_json(_find_one(tc_dir, "*Requester*.json"))
    provider_doc = _load_json(_find_one(tc_dir, "*Provider*.json"))
    ground_truth = _load_json(_find_one(tc_dir, "*ground_truth*.json"))

    required_containers = _capability_containers(requester_doc)
    if not required_containers:
        raise ValueError(f"No capability containers found in requester doc for {tc_dir}")

    return Case(
        test_id=ground_truth.get("test_id", tc_dir.name),
        tc_dir=tc_dir,
        required_container=required_containers[0],
        provided_containers=_capability_containers(provider_doc),
        concept_descriptions=merge_concept_descriptions(provider_doc, requester_doc),
        ground_truth=ground_truth,
    )
