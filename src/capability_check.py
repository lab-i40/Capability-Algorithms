import json
import copy
import asyncio

from openai import AsyncOpenAI
from pathlib import Path
from typing import Any


# UTILS ==================================================================
def _remove_non_english_descriptions_from_sm(data: dict[str, Any]):
    for k, v in list(data.items()):
        if k == "description" and isinstance(v, list):
            data[k] = [d for d in v if d.get("language") == "en"]
            continue

        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _remove_non_english_descriptions_from_sm(item)

        if isinstance(v, dict):
            _remove_non_english_descriptions_from_sm(v)


def _remove_qualifiers_from_sm(data: dict[str, Any]):
    for k, v in list(data.items()):
        if k == "qualifiers":
            del data[k]
            continue

        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _remove_qualifiers_from_sm(item)

        if isinstance(v, dict):
            _remove_qualifiers_from_sm(v)


def _remove_semantic_id_from_sm(data: dict[str, Any]):
    for k, v in list(data.items()):
        if k == "semanticId":
            del data[k]
            continue

        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _remove_semantic_id_from_sm(item)

        if isinstance(v, dict):
            _remove_semantic_id_from_sm(v)


def _remove_model_type_from_sm(data: dict):
    for k, v in list(data.items()):
        if k == "modelType":
            del data[k]
            continue

        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _remove_model_type_from_sm(item)

        if isinstance(v, dict):
            _remove_model_type_from_sm(v)


def _stringify_placeholder_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _load_prompt_template(template_name: str) -> str:
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    template_path = prompts_dir / template_name
    return template_path.read_text(encoding="utf-8")


def _render_prompt_template(template: str, placeholders: dict[str, Any]) -> str:
    rendered = template
    for raw_key, raw_value in placeholders.items():
        key = str(raw_key)
        value = _stringify_placeholder_value(raw_value)

        rendered = rendered.replace(f"{{{{{key}}}}}", value)
        rendered = rendered.replace(f"{{{key}}}", value)
        rendered = rendered.replace(f"${{{key}}}", value)
        rendered = rendered.replace(f"${key}", value)

    return rendered


def _get_prompts_for_capability_check(required_capability: dict[str, Any],
                                      provided_capability: dict[str, Any]) -> tuple[str, str]:
    system_template = _load_prompt_template("system_prompt.md")
    user_template = _load_prompt_template("user_prompt.md")
    placeholders = {
        "ProviderSubmodel": provided_capability,
        "RequesterSubmodel": required_capability,
    }
    system_prompt = _render_prompt_template(system_template, placeholders)
    user_prompt = _render_prompt_template(user_template, placeholders)
    return system_prompt, user_prompt


def to_bool_if_possible(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        match value.strip().lower():
            case "true": return True
            case "false": return False
    return None


def to_float_if_numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def extract_json_from(text: str) -> dict | None:
    if not isinstance(text, str):
        return None
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    try:
        payload = json.loads(text[start:end+1])
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return None


def evaluate_ai_response(data: str) -> dict[str, Any]:
    extracted_json = extract_json_from(text=data)
    if extracted_json is None:
        raise ValueError("No valid JSON block found in text.")

    capable_raw = extracted_json.get("capable")
    reason = extracted_json.get("description")

    if capable_raw is None or reason is None:
        raise KeyError("Missing required fields 'capable' and/or 'reason'.")

    capable = to_bool_if_possible(capable_raw)
    if capable is None:
        raise TypeError("Field 'capable' is not a valid bool.")

    if not isinstance(reason, str):
        raise TypeError("Field 'reason' must be a string.")

    return {"capable": capable, "reason": reason}


# CAPABILITY CHECK ==================================================================
async def capability_test_completion(model: str,
                                     llm_api_key: str,
                                     base_url: str,
                                     required_capability: dict[str, Any],
                                     provided_capability: dict[str, Any]):

    rc = copy.deepcopy(required_capability)
    pc = copy.deepcopy(provided_capability)
    # data cleanup
    _remove_non_english_descriptions_from_sm(rc)
    _remove_non_english_descriptions_from_sm(pc)
    _remove_qualifiers_from_sm(rc)
    _remove_qualifiers_from_sm(pc)
    _remove_semantic_id_from_sm(rc)
    _remove_semantic_id_from_sm(pc)
    _remove_model_type_from_sm(rc)
    _remove_model_type_from_sm(pc)

    # get prompts
    system_prompt, user_prompt = _get_prompts_for_capability_check(rc, pc)

    # call LLM
    client = AsyncOpenAI(api_key=llm_api_key, base_url=base_url)
    response = await client.chat.completions.create(
        model=model,
        max_completion_tokens=10000,
        temperature=0.7,
        top_p=0.95,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    raw_output = response.choices[0].message.content

    try:
        evaluation = evaluate_ai_response(raw_output) # type: ignore
        return {
            "capable": evaluation["capable"],
            "reason": evaluation["reason"],
            "raw_output": raw_output,
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None
        }

    except (ValueError, KeyError, TypeError) as e:
        raise ValueError(f"Failed to evaluate AI response: {e}\nRaw output was:\n{raw_output}")


# LOCAL TESTING ==================================================================
if __name__ == "__main__":
    model = "Qwen/Qwen3.5-397B-A17B"
    base_url = "https://api.together.xyz/v1/"
    api_key = "your_api_key_here"

    project_root = Path(__file__).resolve().parent.parent
    dataset_path = project_root / "dataset" / "group_1.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    raw_dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(raw_dataset, list) or not raw_dataset:
        raise ValueError(f"Dataset must be a non-empty list: {dataset_path}")

    selected_case = raw_dataset[0]

    required_capability = selected_case.get("requester_data")
    provided_capability = selected_case.get("provider_data")

    if not isinstance(required_capability, dict) or not isinstance(provided_capability, dict):
        raise ValueError("First case in group_1.json must contain 'requester_data' and 'provider_data' as objects.")

    async def main():
        result = await capability_test_completion(
            model=model,
            llm_api_key=api_key,
            base_url=base_url,
            required_capability=required_capability,
            provided_capability=provided_capability
        )

        print(json.dumps({
            "dataset": "group_1.json",
            "index": 0,
            "test_id": selected_case.get("test_id"),
            "scenario_id": selected_case.get("scenario_id"),
            "expected_result": selected_case.get("expected_result"),
            "result": result,
        }, ensure_ascii=False, indent=2))

    asyncio.run(main())