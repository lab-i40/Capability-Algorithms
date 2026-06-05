from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from capability_matching import CapabilityCheckResult

CAPABILITY_DESCRIPTION_SM_SEMANTIC_ID = "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0"
CAPABILITY_SET_SEMANTIC_ID = "https://admin-shell.io/idta/CapabilityDescription/CapabilitySet/1/0"
CAPABILITY_CONTAINER_SEMANTIC_ID = "https://admin-shell.io/idta/CapabilityDescription/CapabilityContainer/1/0"
PROPERTY_SET_SEMANTIC_ID = "https://admin-shell.io/idta/CapabilityDescription/PropertySet/1/0"


def get_semantic_id_value(element: dict[str, Any]) -> str | None:
    try:
        return element["semanticId"]["keys"][0]["value"]
    except (KeyError, IndexError):
        return None


def get_capability_containers(aas: dict[str, Any], submodels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    submodel_ids = {
        key["value"]
        for ref in aas.get("submodels", [])
        for key in ref.get("keys", [])
        if key.get("type") == "Submodel"
    }

    containers = []
    for submodel in submodels:
        if submodel.get("id") not in submodel_ids:
            continue
        if get_semantic_id_value(submodel) != CAPABILITY_DESCRIPTION_SM_SEMANTIC_ID:
            continue

        for element in submodel.get("submodelElements", []):
            if get_semantic_id_value(element) != CAPABILITY_SET_SEMANTIC_ID:
                continue

            for item in element.get("value", []):
                if get_semantic_id_value(item) == CAPABILITY_CONTAINER_SEMANTIC_ID:
                    containers.append(item)

    return containers


def get_property_sets(capability_container: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in capability_container.get("value", [])
        if get_semantic_id_value(item) == PROPERTY_SET_SEMANTIC_ID
    ]


def get_concept_descriptions(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return doc.get("conceptDescriptions", [])


def merge_concept_descriptions(doc_a: dict[str, Any], doc_b: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for cd in get_concept_descriptions(doc_a) + get_concept_descriptions(doc_b):
        id_ = cd.get("id")
        if id_ is None or id_ in seen:
            continue
        seen.add(id_)
        merged.append(cd)
    return merged


def write_result(result: CapabilityCheckResult, path: Path) -> None:
    lines: list[str] = []
    sep = "=" * 60

    lines += [
        sep,
        "CAPABILITY CHECK RESULT",
        sep,
        f"Matching:           {result.matching}",
        f"Steps completed:    {result.step_counter}",
        f"Semantic match:     {result.semantic_result}",
        f"Requirement match:  {result.requirement_result}",
        "",
    ]

    lines += [
        "── STEP 1: Semantic Matching ──",
        "",
        "[ Reasoning ]",
        result.semantic_response.thinking,
        "",
        "[ Result ]",
        f"  Primary capability:     {result.semantic_response.result.primary_capability}",
        f"  Auxiliary capabilities: {result.semantic_response.result.auxiliary_capabilities}",
        f"  Match:                  {result.semantic_response.result.match}",
        "",
    ]

    if result.requirement_response:
        lines += ["── STEP 2: Requirement Matching ──", ""]
        for ps_id, resp in result.requirement_response.results.items():
            lines += [
                f"[ {ps_id} ]",
                "",
                "  Reasoning:",
                resp.thinking,
                "",
                f"  Verdict:       {resp.result.verdict.value}",
                f"  Justification: {resp.result.justification}",
                "",
            ]

    lines += [
        "── Usage ──",
        "",
        "  Step 1:",
        f"    prompt={result.semantic_response.usage.prompt_tokens}"
        f"  completion={result.semantic_response.usage.completion_tokens}"
        f"  total={result.semantic_response.usage.total_tokens}",
    ]

    if result.requirement_response:
        for ps_id, resp in result.requirement_response.results.items():
            u = resp.usage
            lines.append(
                f"  {ps_id}: prompt={u.prompt_tokens}"
                f"  completion={u.completion_tokens}"
                f"  total={u.total_tokens}"
            )

    lines.append(sep)

    path.write_text("\n".join(lines), encoding="utf-8")
