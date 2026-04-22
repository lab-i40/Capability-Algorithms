# Dataset Info

This directory contains the test datasets used in the evaluation of LLM-based Capability Check described in the paper "Large Language Models as a Decision-making Core for Semantic Capability Check in Asset Administration Shell-based Intelligent Manufacturing".

## Test Groups

Each file corresponds to one of the four test groups defined in the evaluation methodology. Every group contains balanced sets of positive cases `(capable: true)` and negative cases `(capable: false)`, covering a specific dimension of the compatibility verification task.

**G1** — Semantic Relationship between Capabilities evaluates whether the model correctly identifies semantic (mis)match between the capability type declared in the provider submodel and the one requested by the requester, operating exclusively over capability identifiers without altering any numerical values or internal structure.

**G2** — Insufficient Inferential Evidence evaluates the model's behavior when the provider submodel lacks information needed to satisfy a requirement declared by the requester. The expected behavior is conservative: in the absence of evidence, the model should reject the request.

**G3** — Limiting Properties and Parameterization evaluates the model's ability to verify numerical compatibility between operational constraints declared by the provider and the values required by the requester, including range checking with inclusive and exclusive bounds.

**G4** — Invalid or Inconsistent Data evaluates the model's ability to detect structural inconsistencies such as `valueType` mismatches and incorrectly formatted values, distinguishing them from structurally valid submodels.

## Data Origin

The submodel instances were derived from a Screwing capability submodel following the structural rules defined in the Industrie 4.0 Capabilities, Skills and Services white paper.

The base instances were created and exported from the AASX Package Explorer v3, using a .aasx file containing the Screwing submodel. Multiple instances were created within the tool and exported as JSON.

From those base instances, additional synthetic data was generated through two complementary approaches: automated scripts produced parametric variations by modifying numerical property values while preserving the submodel structure, and manual edits introduced structural variations — such as removal of properties, type inconsistencies, and semantic mismatches — to cover the full range of test scenarios required by each group.