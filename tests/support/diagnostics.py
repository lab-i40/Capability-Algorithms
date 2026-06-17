"""Classificação diagnóstica de um caso (taxonomia de ``test_2.tex``).

Compara o resultado emitido (``CapabilityCheckResult``) com o ground truth:

- **decisão** (``y_s`` vs ``ŷ_s``): :func:`outcome_ok`;
- **caminho** (``τ_s`` vs ``τ̂_s``, a trajetória nas etapas estocásticas):
  :func:`path_ok`.

A combinação dá a situação σ_s:

==========================  =====================================
``correct-clean``           ``ŷ == y`` e ``τ̂ == τ``
``correct-with-recovery``   ``ŷ == y`` e ``τ̂ != τ``
``incorrect``               ``ŷ != y``
==========================  =====================================

O caso "decisão incorreta com caminho correto" é vazio por construção.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from capability_matching import CapabilityCheckResult

CORRECT_CLEAN = "correct-clean"
CORRECT_WITH_RECOVERY = "correct-with-recovery"
INCORRECT = "incorrect"


def outcome_ok(result: "CapabilityCheckResult", gt: dict[str, Any]) -> bool:
    """``ŷ_s == y_s``: o veredito final bate com ``matching_result``."""
    return bool(result.matching) == bool(gt["matching_result"])


def _semantic_path_ok(result: "CapabilityCheckResult", gt: dict[str, Any]) -> bool:
    """Step 1: ``match`` sempre; primary/aux só quando o GT os preenche."""
    sem_gt = gt.get("sematic_matching_gt", {})
    actual = result.semantic_response.result

    if actual.match != sem_gt.get("match"):
        return False

    expected_primary = sem_gt.get("primary_capability")
    if expected_primary is not None and actual.primary_capability != expected_primary:
        return False

    expected_aux = sem_gt.get("auxiliary_capabilities")
    if expected_aux and set(actual.auxiliary_capabilities) != set(expected_aux):
        return False

    return True


def _requirement_path_ok(result: "CapabilityCheckResult", gt: dict[str, Any]) -> bool:
    """Step 2: cada property set do GT tem o ``verdict`` esperado."""
    req_gt = gt.get("requirement_matching_gt", {})
    if not req_gt:
        return True

    if result.requirement_response is None:
        return False

    actual = result.requirement_response.results
    for ps_id, expected in req_gt.items():
        response = actual.get(ps_id)
        if response is None:
            return False
        if response.result.verdict.value != expected["verdict"]:
            return False

    return True


def path_ok(result: "CapabilityCheckResult", gt: dict[str, Any]) -> bool:
    """``τ̂_s == τ_s``: etapa de término + Step 1 + Step 2 conferem."""
    if result.step_counter != gt["final_step"]:
        return False
    if not _semantic_path_ok(result, gt):
        return False
    return _requirement_path_ok(result, gt)


def classify(result: "CapabilityCheckResult", gt: dict[str, Any]) -> str:
    """Retorna σ_s ∈ {``correct-clean``, ``correct-with-recovery``, ``incorrect``}."""
    if not outcome_ok(result, gt):
        return INCORRECT
    if path_ok(result, gt):
        return CORRECT_CLEAN
    return CORRECT_WITH_RECOVERY
