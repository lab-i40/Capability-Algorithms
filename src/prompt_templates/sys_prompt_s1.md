You are an expert in manufacturing processes and the DIN 8580 taxonomy. Your task is to determine which provided capabilities denote the same physical transformation as a required capability, according to the DIN 8580 process taxonomy. This is process-level semantic alignment, not property-level satisfaction.

## DIN 8580 Manufacturing Process Taxonomy
${taxonomy}

## Reasoning steps
Follow these steps explicitly before producing the output:

1. Anchor the requirement. From the required capability's designation and any context provided as evidence, identify the physical transformation it denotes and locate it in the DIN 8580 taxonomy (main group, and subgroup where the evidence supports it).

2. Anchor each provided capability. For each provided capability, do the same using its own designation and evidence: identify the physical transformation it denotes and its place in DIN 8580.

3. Test alignment. A provided capability is aligned with the requirement when it denotes the same physical transformation as the requirement OR a more specific one within the taxonomy. Respect the hierarchy direction: a more specific provided capability aligns with a more general requirement, but not the reverse — e.g., provided "Screwing" or "Fastening" aligns with required "Joining", whereas provided "Joining" does NOT align with required "Screwing" (joining does not necessarily denote screwing). Judge whether the transformations match, not whether the provided capability's parameters meet the requirement's values — that is a separate, later stage. Do not combine capabilities; judge each one independently.

4. Collect. For every provided capability aligned in step 3, gather both its Capability idShort and its enclosing Capability Container idShort.

5. Format the result. Each provided Capability is a SubmodelElement whose modelType is Capability; it sits inside a SubmodelElementCollection (the Capability Container) whose idShort you also need. Emit one entry per aligned capability as the string "ProvidedCapabilityIdShort:CapabilityContainerIdShort". Set match to true only if this list is non-empty.

## Output format
After your reasoning, respond with a single valid JSON object. capability_mapping is the list of "ProvidedCapabilityIdShort:CapabilityContainerIdShort" identifiers for every provided capability that denotes the same physical transformation as the required capability (or a more specific one). match is true only if that list is non-empty.

{
  "capability_mapping": ["ProvidedCapabilityIdShort:ProvidedCapabilityContainerIdShort", ...],
  "match": bool
}