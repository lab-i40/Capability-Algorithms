import json
import os
from pathlib import Path

import pytest

from capability_check import capability_test_completion

CASES = json.loads(
    (
        Path(__file__).resolve().parents[2] / "dataset" / "group_3.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", CASES, ids=[c["test_id"] for c in CASES])
async def test_group_3(case, request):
    result = await capability_test_completion(
        model=os.environ["LLM_MODEL"],
        llm_api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["AI_API_BASE_URL"],
        required_capability=case["requester_data"],
        provided_capability=case["provider_data"],
    )
    request.node.actual_result_obj = result
    assert result["capable"] == case["expected_result"], result.get("reason")
