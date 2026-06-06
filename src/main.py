import asyncio
import json
import os

from pathlib import Path
from typing import Any

from capability_matching import capability_check
from utils import get_capability_containers, merge_concept_descriptions, write_result



def load_tc00_example() -> dict[str, Any]:
    dataset_dir = Path(__file__).parent.parent / "dataset" / "tc00-example"
    result: dict[str, Any] = {}
    for file in sorted(dataset_dir.glob("*.json")):
        with open(file, encoding="utf-8") as f:
            result[file.stem] = json.load(f)
    return result


def get_capability_set_from(filename: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    doc = data[filename]
    return get_capability_containers(doc["assetAdministrationShells"][0], doc["submodels"])


async def main() -> None:
    api_key = "tgp_v1_fITvZ-dz6vZ8W1aEMZLk8F2hOUqOcct_ZdgGy4RPJtk"

    data = load_tc00_example()

    provider_key = "A1_1_positive_Provider_screwing"
    requester_key = "A1_1_positive_Requester_joining"

    provided_containers = get_capability_set_from(provider_key, data)
    required_containers = get_capability_set_from(requester_key, data)
    concept_descriptions = merge_concept_descriptions(data[provider_key], data[requester_key])

    result = await capability_check(
        required_capability_container=required_containers[0],
        provided_capabilities=provided_containers,
        concept_descriptions=concept_descriptions,
        api_key=api_key,
        parallel=True
    )

    output_path = Path(__file__).parent.parent / "result.txt"
    write_result(result, output_path)
    print(f"Result written to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
