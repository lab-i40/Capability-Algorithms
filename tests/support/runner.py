"""Wrapper assíncrono fino sobre :func:`capability_matching.capability_check`.

D1: modelo/endpoint (Together/Qwen) ficam fixos no ``src``; o teste só injeta a
``api_key`` lida de ``OPENAI_API_KEY``.
D3: toda execução chama a LLM de verdade — não há caminho offline/mock.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from capability_matching import capability_check

if TYPE_CHECKING:
    from capability_matching import CapabilityCheckResult

    from .loader import Case


async def run_check(
    case: "Case",
    api_key: str | None = None,
    parallel: bool = True,
) -> "CapabilityCheckResult":
    """Executa o algoritmo de dois passos para ``case``.

    Se ``api_key`` for ``None``, lê de ``os.environ["OPENAI_API_KEY"]``.
    """
    if api_key is None:
        api_key = os.environ["OPENAI_API_KEY"]

    return await capability_check(
        required_capability_container=case.required_container,
        provided_capabilities=case.provided_containers,
        concept_descriptions=case.concept_descriptions,
        api_key=api_key,
        parallel=parallel,
    )
