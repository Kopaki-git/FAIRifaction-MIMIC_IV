# AGENTS.md — FAIR MIMIC-IV Project

## Purpose

Instructions for coding agents working in the `FAIRifaction-MIMIC_IV` repository.

This is a University of Twente FAIR Data Engineering course project. It represents a bounded MIMIC-IV Demo v2.2 extract as reproducible, checked RDF using an approved FHIR R4-aligned semantic model.

The RDF generator, Turtle export and acceptance tests are **complete**. Work now centres on keeping them correct and on the remaining course deliverables, not on new modelling or serialization design.

**Do not redesign the clinical-semantic model or reopen completed implementation decisions.**

## Read first: hierarchy of authority

Before substantive work, inspect the current Git state and read:

1. `docs/semantic_model_mapping.md` — **authoritative clinical-semantic model** and terminology mappings.
2. `docs/rdf_serialization.md` — **implemented serialization decisions**: W3ID base, IRI patterns, identifier and CodeSystem reuse, extensions, RDF dialect, verification scope and limitations.
3. `docs/semantic_mapping_provenance.md` — mapping justification and evidence limitations.
4. `README.md` — current project overview, source layout and reproduction instructions.
5. `notebooks/01_dataset_exploration_and_extraction.ipynb` — authoritative extraction logic, when derivation details are relevant.

`src/generate_rdf.py` and `tests/test_rdf.py` implement documents 1 and 2. Their section comments and docstrings explain the design reasoning; read them before changing either file.

`docs/rdf_implementation_handoff.md` is the pre-implementation record. Its §6 acceptance criteria are still what the tests implement, but its route, deferred decisions and next-session plan are superseded by `docs/rdf_serialization.md`.

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
- Do not treat the semantic DAG as a complete literal FHIR-RDF serialization specification. The implemented serialization is defined in `docs/rdf_serialization.md`.

## Established implementation decisions

Resolved with the user and recorded in `docs/rdf_serialization.md` (D1–D7). Do not reopen them without a demonstrated blocking problem and an explicit user decision.

- **D1 W3ID base:** `https://w3id.org/FAIR-course-UT/2026/group04/`, confirmed by the teacher. Redirects are live through the course relay (rules in `w3id/`, relay PRs #12 and #14), so all IRIs resolve.
- **D2 Resource IRIs:** hash namespace `<base>data#`, deterministic patterns built only from source keys.
- **D3 Nested elements:** blank nodes for all FHIR datatypes and backbone elements; IRIs only for the six resource kinds.
- **D4–D5:** `Identifier.system` URIs and MIMIC-local CodeSystems reused from the MIMIC-FHIR IG 1.3.0 (draft).
- **D6 Extensions:** the warning and admission-type extensions have project URLs under the W3ID base and are provisional, with no formal `StructureDefinition`s.
- **D7 Serialization:** simplified FHIR-predicate RDF, not strict FHIR-RDF; `uri` values as plain strings (R4 style); timestamps as `xsd:dateTime` without timezone; ShEx validation deferred.

The generator fails on any source value outside the approved mapping tables. Never add silent defaults or fallback mappings to make it run.

`rdf/mimic_icu_vitals_4h.ttl` is generated output. Do not edit it by hand; change the generator, regenerate and rerun the tests.

## Verification

Reproduce and check with:

```bash
venv/bin/python src/generate_rdf.py
venv/bin/python -m pytest tests/ -v
```

`tests/test_rdf.py` covers:

1. Successful parsing by RDFLib and an independent parser (pyoxigraph).
2. Expected resource and interval counts.
3. Correct Patient, Hospital Encounter, ICU Encounter, Condition and Location references.
4. Preservation of numerical values (including lexical form), source units, charted times, periods and identifiers.
5. Correct LOINC, UCUM, HL7, SNOMED and ICD codings against independently transcribed tables.
6. Edge cases: SpO₂ dual coding, multiple care-unit intervals, the warning row, unmapped priorities, Neuro SICU's two types and historical ICD codes.
7. Scope constraints and deliberate omissions.
8. Reproducibility: fresh generations and the committed Turtle have identical RDFC-1.0 canonical forms, with a negative control.

Any change to the generator, tests or committed RDF must leave the full suite passing, including the reproducibility check against the committed Turtle.

Expected values in the tests are transcribed from the model, not computed by the generator. Do not change a test expectation to match generator output; a mismatch is a finding to report.

A passing RDF parser does **not** establish semantic fidelity, and the suite as a whole does **not** establish strict FHIR conformance.

Failures and limitations must be reported explicitly rather than repaired by unsupported clinical assumptions.

## Known limitations

These are documented in `docs/rdf_serialization.md` §6 and are accepted, not outstanding bugs:

- Not strict FHIR-RDF; no ShEx validation.
- No timezone on timestamps (an R4 conformance gap).
- Provisional extensions; their URLs redirect to the `docs/` folder, not to definitions.
- Browsers resolving a `data#…` IRI land on the `rdf/` folder until a public landing page exists.
- Reused MIMIC-FHIR systems come from a draft IG.
- Canonical ICD codes are format-normalized only, not re-validated against CMS/CDC releases.

Represent them accurately in any report, presentation or documentation. Do not describe them as resolved.

## Current priorities and workstream boundaries

Deadlines: project presentation **26 October 2026**; final deliverables **1 November 2026** (moved forward from 7 November by the professor on 22 October).

In this workstream:

- Keep the generator, tests, Turtle export and documentation consistent with each other.
- Support the report and presentation with accurate claims: FHIR-aligned RDF, baseline FAIR properties of MIMIC-IV and MIMIC-FHIR distinguished from the project's added value, and limitations stated.

Coordinated separately by a teammate, and out of scope unless the user explicitly brings them in:

- SHACL metadata schemas and records (`metadata/`).
- FAIR Data Point publication.
- W3ID redirect registration.
- SPARQL and cross-dataset integration queries.
- `rdf/mimic_icu_vitals_4h_csv_non_FHIR.ttl`.

Do not modify these artifacts. If work here depends on one of them, surface the dependency instead of changing it.

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
