"""Módulo único e plano da suíte (D2): parametriza os 16 casos da matriz.

**Sem asserts** (ver ``docs/plano-refatoracao-testes.md`` §1/Fase 3): o teste só
executa o caso e registra ``case``/``loaded``/``result`` no nó. A correção
(acertou/falhou) é apurada na camada de relatório (``conftest`` + ``diagnostics``)
comparando o resultado contra o ground truth — não pelo status pass/fail do pytest.

D3 = só chamadas reais: ``run_check`` chama a LLM de verdade; exige
``OPENAI_API_KEY`` no ambiente.
"""

import os

import pytest

from tests.support.loader import load_case
from tests.support.matrix import ALL_CASES
from tests.support.runner import run_check


@pytest.mark.parametrize("case", ALL_CASES, ids=[c["test_id"] for c in ALL_CASES])
async def test_capability(case, request):
    request.node.case = case  # registrado primeiro: disponível mesmo se houver erro
    loaded = load_case(case["dir"])
    request.node.loaded = loaded
    result = await run_check(loaded, api_key=os.environ["OPENAI_API_KEY"])
    request.node.actual_result = result
    # sem assert — a apuração acontece no relatório vs ground truth
