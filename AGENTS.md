# AGENTS.md — FAIR MIMIC-IV Project

## Purpose

Instructions for coding agents working in the `FAIRifaction-MIMIC_IV` repository.

This is a University of Twente FAIR Data Engineering course project. The immediate technical objective is to generate reproducible, validated RDF from a bounded MIMIC-IV Demo v2.2 dataset using an already approved FHIR R4-aligned semantic model.

**Do not redesign the clinical-semantic model as part of implementation.**

## Read first: hierarchy of authority

Before substantive work, inspect the current Git state and read:

1. `docs/semantic_model_mapping.md` — **authoritative clinical-semantic model** and terminology mappings.
2. `docs/rdf_implementation_handoff.md` — current implementation goals, deferred decisions and acceptance criteria.
3. `docs/semantic_mapping_provenance.md` — mapping justification and evidence limitations.
4. `README.md` — current project overview, source layout and reproduction instructions.
5. `notebooks/01_dataset_exploration_and_extraction.ipynb` — authoritative extraction logic, when derivation details are relevant.

Do not reconstruct prior semantic models from Git history. If documentation conflicts with the canonical specification, stop and surface the discrepancy.

## Dataset invariants

The canonical unFAIRified source is the five-table resource at:

`data/derived/mimic_icu_vitals_4h/`

Expected counts:

- 2,501 Observations: 859 heart rate, 860 respiratory rate, 782 SpO₂.
- 94 patients.
- 121 hospital admissions.
- 133 ICU stays.
- 167 time-bounded care-unit intervals.
- 121 first-ranked billed diagnoses.

The first-four-hour selection rule and the three MIMIC item identifiers (`220045`, `220210`, `220277`) are fixed.

Do not alter the source tables, extraction boundary, patient/admission/stay relationships, original identifiers, shifted timestamps, warning flags or unusual recorded values to make downstream transformation easier.

Original upstream MIMIC data belongs under ignored `data/icu/` and `data/hosp/` directories. Do not commit it.

## Semantic and implementation boundaries

Use the canonical model's FHIR R4 structures and approved terminology mappings. Preserve MIMIC-local values alongside qualified standard representations.

In particular:

- Do not invent new mappings, admission priorities, diagnosis meanings or care-unit equivalences.
- Do not treat broader HL7 care-unit classifications as exact equivalence mappings.
- Do not promote `transfer_id` or `eventtype` to additional clinical entities.
- Do not assert `meta.profile` or strict FHIR conformance without actual validation.
- Do not claim that FHIR conversion alone constitutes a new FAIRification contribution over existing MIMIC-FHIR work.
- Do not treat the semantic DAG as a complete literal FHIR-RDF serialization specification.

The proposed transformation route is Python with RDFLib. RDFTransform in OpenRefine remains an optional targeted verification fallback, not an obligatory parallel pipeline.

## Deferred choices

Before creating RDF resources, resolve the minimum necessary identifier decisions with the user:

- Correct W3ID academic-year prefix and group number.
- Deterministic RDF resource URI patterns.
- Local identifier and coding-system namespaces.
- Project-extension representation and namespace requirements.

The existing handoff documents the URI-prefix discrepancy. Do not silently adopt a historical namespace.

Metadata schemas, FAIR Data Point configuration and W3ID redirects are separate workstreams unless explicitly brought into scope.

## Validation requirements

Generated RDF must be tested for:

1. Successful RDF parsing.
2. Expected resource and interval counts.
3. Correct Patient, Hospital Encounter and ICU Encounter references.
4. Preservation of numerical values, source units and charted times.
5. Correct LOINC, UCUM, HL7, SNOMED and ICD codings.
6. Relevant edge cases, including SpO₂ dual coding, multiple care-unit intervals, warnings, unmapped priorities and historical ICD codes.
7. Deterministic, reproducible graph generation.

A passing RDF parser does **not** establish semantic fidelity or strict FHIR conformance.

Failures and limitations must be reported explicitly rather than repaired by unsupported clinical assumptions.

## Change control

**Propose → approve → execute.**

Before creating, replacing, deleting or committing substantive project artifacts:

1. Inspect current repository state.
2. Identify the exact files and intended changes.
3. Surface consequential implementation decisions one at a time.
4. Summarize the proposed specification and obtain explicit user approval.
5. Apply only the approved changes.
6. Run appropriate checks and report the results, including failures.
7. Verify the resulting Git changes and commit state.

Do not treat a diagnostic question or discussion of alternatives as permission to modify files.

If implementation evidence contradicts a frozen decision, stop and request a decision rather than silently changing the semantic model.

Prioritize a working, checked RDF export and clear reproducibility over unnecessary infrastructure or elaborate abstractions.
