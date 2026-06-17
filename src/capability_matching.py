import json
import asyncio
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from string import Template
from typing import Any

import aiohttp

from utils import get_property_sets

TOGETHER_BASE_URL = "https://api.together.ai/v1/chat/completions"
TOGETHER_MODEL = "Qwen/Qwen3.7-Max"

@dataclass
class TokenDetails:
    reasoning_tokens: int = 0
    cached_tokens: int = 0


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    completion_tokens_details: TokenDetails
    prompt_tokens_details: TokenDetails

    @staticmethod
    def from_dict(d: dict) -> "Usage":
        return Usage(
            prompt_tokens=d["prompt_tokens"],
            completion_tokens=d["completion_tokens"],
            total_tokens=d["total_tokens"],
            completion_tokens_details=TokenDetails(**d.get("completion_tokens_details", {})),
            prompt_tokens_details=TokenDetails(**d.get("prompt_tokens_details", {})),
        )


@dataclass
class CapabilityMatchResult:
    primary_capability: str | None
    auxiliary_capabilities: list[str]
    match: bool


@dataclass
class MatchingResponse:
    thinking: str
    result: CapabilityMatchResult
    usage: Usage


class Verdict(str, Enum):
    satisfied = "satisfied"
    unsatisfied = "unsatisfied"
    indeterminate = "indeterminate"


@dataclass
class RequirementMatchResult:
    verdict: Verdict
    justification: str


@dataclass
class RequirementMatchResponse:
    thinking: str
    result: RequirementMatchResult
    usage: Usage


@dataclass
class PropertyCheckResult:
    results: dict[str, RequirementMatchResponse]
    capable: bool


@dataclass
class CapabilityCheckResult:
    matching: bool
    step_counter: int
    semantic_result: bool
    requirement_result: bool
    semantic_response: MatchingResponse
    requirement_response: PropertyCheckResult | None


def parse_match_result(content: str) -> CapabilityMatchResult:
    block = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if not block:
        raise ValueError(f"No JSON block found in model response:\n{content}")
    data = json.loads(block.group(1))
    return CapabilityMatchResult(
        primary_capability=data["primary_capability"],
        auxiliary_capabilities=data["auxiliary_capabilities"],
        match=data["match"],
    )


def parse_requirement_result(content: str) -> RequirementMatchResult:
    block = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if not block:
        raise ValueError(f"No JSON block found in model response:\n{content}")
    data = json.loads(block.group(1))
    return RequirementMatchResult(
        verdict=Verdict(data["verdict"]),
        justification=data["justification"],
    )


def build_s2_prompts(
    property_set: dict[str, Any],
    capability_containers: list[dict[str, Any]],
    concept_descriptions: list[dict[str, Any]],
) -> tuple[str, str]:
    src = Path(__file__).parent
    sys_prompt = (src / "prompt_templates" / "sys_prompt_s2.md").read_text(encoding="utf-8")
    usr_template = Template((src / "prompt_templates" / "usr_prompt_s2.md").read_text(encoding="utf-8"))

    usr_prompt = usr_template.substitute({
        "need": json.dumps(property_set),
        "offered_capabilities": json.dumps(capability_containers),
        "concept_descriptions": json.dumps(concept_descriptions),
    })

    return sys_prompt, usr_prompt


def build_s1_prompts(required_capability: dict[str, Any], provided_capabilities: list[dict[str, Any]]) -> tuple[str, str]:
    src = Path(__file__).parent
    taxonomy = (src / "resources" / "din8580_taxonomy.txt").read_text(encoding="utf-8")
    sys_template = Template((src / "prompt_templates" / "sys_prompt_s1.md").read_text(encoding="utf-8"))
    usr_template = Template((src / "prompt_templates" / "usr_prompt_s1.md").read_text(encoding="utf-8"))

    sys_prompt = sys_template.substitute({"taxonomy": taxonomy})
    usr_prompt = usr_template.substitute({
        "required_capability_container": json.dumps(required_capability),
        "provided_capability_set": json.dumps(provided_capabilities),
    })

    return sys_prompt, usr_prompt


async def _collect_stream(resp: aiohttp.ClientResponse) -> tuple[str, str, dict[str, Any]]:
    thinking_parts: list[str] = []
    content_parts: list[str] = []
    usage: dict[str, Any] = {}

    async for raw_line in resp.content:
        line = raw_line.decode().strip()
        if not line.startswith("data:"):
            continue
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            break

        chunk = json.loads(data)
        if chunk.get("usage"):
            usage = chunk["usage"]

        choices = chunk.get("choices", [])
        if not choices:
            continue

        delta = choices[0].get("delta", {})
        if delta.get("reasoning"):
            thinking_parts.append(delta["reasoning"])

        if delta.get("content"):
            content_parts.append(delta["content"])

    return "".join(thinking_parts), "".join(content_parts), usage


async def semantic_matching(
    required_capability: dict[str, Any],
    capability_set: list[dict[str, Any]],
    api_key: str,
) -> MatchingResponse:
    """Match a required capability against a set of provided capabilities using DIN 8580 taxonomy.

    Calls the Together AI API with step-1 prompts (taxonomy-aware semantic alignment).
    Streams the response and returns the model's reasoning, the structured match result,
    and token usage.

    Args:
        required_capability: A capability container dict from the requester AAS.
        capability_set: List of capability container dicts from the provider AAS.
        api_key: Together AI API key.

    Returns:
        MatchingResponse with thinking trace, parsed CapabilityMatchResult, and Usage.

    Raises:
        ValueError: If the model response does not contain a valid JSON block.
    """
    sys_prompt, usr_prompt = build_s1_prompts(required_capability, capability_set)

    # Stream response necessária pro modelo escolhido.
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt},
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "reasoning": {"enabled": True},
        "reasoning_effort": "medium",
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(TOGETHER_BASE_URL, headers=headers, json=payload) as resp:
            thinking, content, usage = await _collect_stream(resp)

    return MatchingResponse(
        thinking=thinking,
        result=parse_match_result(content),
        usage=Usage.from_dict(usage),
    )


async def single_requirement_match(
    property_set: dict[str, Any],
    capability_containers: list[dict[str, Any]],
    concept_descriptions: list[dict[str, Any]],
    api_key: str,
) -> RequirementMatchResponse:
    sys_prompt, usr_prompt = build_s2_prompts(property_set, capability_containers, concept_descriptions)

    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": usr_prompt},
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "reasoning": {"enabled": True},
        "reasoning_effort": "medium",
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(TOGETHER_BASE_URL, headers=headers, json=payload) as resp:
            thinking, content, usage = await _collect_stream(resp)

    return RequirementMatchResponse(
        thinking=thinking,
        result=parse_requirement_result(content),
        usage=Usage.from_dict(usage),
    )


async def requirement_matching(
    required_capability_container: dict[str, Any],
    capability_containers: list[dict[str, Any]],
    concept_descriptions: list[dict[str, Any]],
    api_key: str,
    parallel: bool = False,
) -> PropertyCheckResult:
    property_sets = get_property_sets(required_capability_container)

    if parallel:
        responses = await asyncio.gather(*[
            single_requirement_match(ps, capability_containers, concept_descriptions, api_key)
            for ps in property_sets
        ])
        results = {ps["idShort"]: resp for ps, resp in zip(property_sets, responses)}
    else:
        results: dict[str, RequirementMatchResponse] = {}
        for ps in property_sets:
            results[ps["idShort"]] = await single_requirement_match(
                ps, capability_containers, concept_descriptions, api_key
            )

    capable = all(r.result.verdict == Verdict.satisfied for r in results.values())
    return PropertyCheckResult(results=results, capable=capable)


def _filter_matched_containers(
    provided_capabilities: list[dict[str, Any]],
    match_result: CapabilityMatchResult,
) -> list[dict[str, Any]]:
    refs = [r for r in [match_result.primary_capability] + match_result.auxiliary_capabilities if r]
    matched_ids = {ref.split(":")[1] for ref in refs if ":" in ref}
    return [c for c in provided_capabilities if c.get("idShort") in matched_ids]


async def capability_check(
    required_capability_container: dict[str, Any],
    provided_capabilities: list[dict[str, Any]],
    concept_descriptions: list[dict[str, Any]],
    api_key: str,
    parallel: bool = False,
) -> CapabilityCheckResult:
    semantic_response = await semantic_matching(
        required_capability_container, provided_capabilities, api_key
    )

    if not semantic_response.result.match:
        return CapabilityCheckResult(
            matching=False,
            step_counter=1,
            semantic_result=False,
            requirement_result=False,
            semantic_response=semantic_response,
            requirement_response=None,
        )

    filtered = _filter_matched_containers(provided_capabilities, semantic_response.result)

    prop_result = await requirement_matching(
        required_capability_container, filtered, concept_descriptions, api_key, parallel=parallel
    )

    return CapabilityCheckResult(
        matching=prop_result.capable,
        step_counter=2,
        semantic_result=True,
        requirement_result=prop_result.capable,
        semantic_response=semantic_response,
        requirement_response=prop_result,
    )

