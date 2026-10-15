# FAIR MIMIC-IV — RDF Implementation Handoff

**Status:** Proposed implementation handoff  
**Prepared:** 14 October 2026  
**First cleanup synchronization:** 15 October 2026  
**Repository:** [Kopaki-git/FAIRifaction-MIMIC_IV](https://github.com/Kopaki-git/FAIRifaction-MIMIC_IV)  
**Inspected main commit:** `5893d61b6b0135c436d1e6a146452791fa73c96c`

## 1. Purpose and immediate objective

The FAIR Data Engineering project has completed its canonical source-resource reconstruction and clinical-semantic modelling. The immediate objective is to **generate a reproducible RDF Turtle representation of the approved model**, ideally during a focused working session on 15 October, and hand it to the teammate.

The project presentation is scheduled for **26 October 2026**, with the final project deliverables scheduled for **7 November 2026** according to Lecture 1.

Time is constrained. Do not reopen completed semantic-modelling decisions or introduce additional FHIR conformance work unless a demonstrated blocking problem requires it.

## 2. Authoritative project state

The following files constitute the current authoritative technical state.

### Canonical semantic specification

`docs/semantic_model_mapping.md`

This contains the globally audited FHIR R4-based semantic model, including:

- The full RDF-oriented canonical DAG.
- A derived, property-preserving backbone DAG.
- Measurement terminology and UCUM mappings.
- Patient and Encounter relationships.
- Time-resolved ICU care-unit semantics.
- Hospital admission classification and priority.
- First-ranked billed diagnosis semantics.
- Deliberate omissions and remaining implementation decisions.
- An explicit distinction between MIMIC-FHIR baseline interoperability and the project's proposed FAIRification gains.

**This is the semantic source of truth.** Do not substitute an older model, diagram, provenance document or previous assistant-generated mapping.

### Canonical unFAIRified resource

`data/derived/mimic_icu_vitals_4h/`

| File | Rows |
|---|---:|
| `observations.csv` | 2,501 |
| `icu_stays.csv` | 133 |
| `careunit_intervals.csv` | 167 |
| `hospital_admissions.csv` | 121 |
| `first_ranked_diagnoses.csv` | 121 |

The extract covers 94 patients, 121 hospital admissions and 133 ICU stays.

Measurements are heart rate (`220045`), respiratory rate (`220210`) and SpO₂ (`220277`) within the first four hours of represented ICU stays.

`notebooks/01_dataset_exploration_and_extraction.ipynb` is the authoritative reproducible derivation.

The five derived tables represent the **original, unFAIRified project object**. The upstream MIMIC-IV Demo v2.2 source tables are not version-controlled.

## 3. Semantic decisions already frozen

FHIR R4 supplies the clinical structural model. Shared terminology includes LOINC, HL7 terminology, SNOMED CT, UCUM and ICD-9-CM/ICD-10-CM.

The model contains:

- `Observation` — one resource per charted vital-sign observation.
- `Patient` — locally identified by `subject_id`.
- ICU `Encounter` — locally identified by `stay_id`; `status=finished`, `class=ACUTE`.
- Hospital `Encounter` — locally identified by `hadm_id`; `status=finished`, `class=IMP`.
- `Encounter.location` — repeated, time-bounded care-unit intervals.
- `Location` — reusable care-unit kinds with source labels and qualified standardized classifications.
- `Condition` — the first-ranked billed diagnosis for each represented hospitalization.

Source identifiers must remain distinguishable from globally scoped resource identities.

MIMIC source meaning must not be silently replaced by standardized codings.

The nine care-unit categories use the approved HL7 role mappings and only two directly defensible SNOMED co-codings. The standardized role classification may be broader than the source category.

Admission urgency is standardized only for four source categories; the other two retain their original values without invented priorities.

The source `warning` and `admission_type` fields are preserved through narrowly defined extensions.

`transfer_id` and `eventtype` are intentionally omitted from the scoped clinical semantic graph, although retained in the derived source.

**No semantic redesign is authorized by this handoff.**

## 4. Course requirements governing implementation

The Canvas project description explicitly permits an **RDF-generation script** instead of OpenRefine's RDF extension.

The course requires RDF transformation and publication of FAIRified data. It does not explicitly require strict FHIR-RDF serialization or FHIR resource-validator conformance.

The proposed target is therefore:

**Valid, reproducible, FHIR-aligned RDF implementing the canonical semantic model, without claiming strict FHIR R4 serialization conformance.**

Additional requirements include:

- Globally unique, persistent, resolvable W3ID identifiers.
- Original and RDF data committed to GitHub/GitLab.
- Metadata schemas and records.
- FAIR Data Point publication workflow, subject to clarification from the professor.
- Identification of external-dataset linking points and possible integration queries.
- Presentation and final report.

Executing cross-dataset SPARQL queries is optional.

## 5. Proposed RDF implementation route

**Preferred approach, not yet implemented:** Python with RDFLib.

Conceptual workflow:

```text
Five canonical source CSVs
        ↓
Reproducible Python RDF transformation
        ↓
RDF Turtle
        ↓
Independent parsing and integrity checks
        ↓
Repository deliverable and teammate handoff
```

Use deterministic IRIs so references to the same Patient, Encounter, Condition or Location resolve to the same graph entity across source tables.

The five source tables should retain their natural grains; do not automatically flatten them into a single CSV.

OpenRefine/RDFTransform remains a **targeted verification fallback** if a meaningful uncertainty survives the Python output checks.

That fallback should use a small, representative OpenRefine project, not reproduce the entire five-table pipeline unless a concrete need emerges.

A provisional effort budget is 3–6 focused hours, but this is an estimate, not demonstrated implementation time.

## 6. Minimum RDF acceptance criteria

Before the RDF export is accepted:

1. Generated Turtle parses successfully using an independent RDF parser.
2. Resource counts match the canonical source, including 2,501 Observations, 94 Patients, 133 ICU Encounters, 121 Hospital Encounters and 121 Conditions.
3. All 167 encounter-location interval entries are represented.
4. Patient, hospital admission and ICU-stay references are correct.
5. Numerical values, charted times and original unit strings are preserved.
6. LOINC, UCUM, HL7 care-setting roles, approved SNOMED mappings and ICD codings are checked against the frozen specification.
7. Representative edge cases are inspected: dual SpO₂ coding, multi-interval ICU stays, admission types without standardized priority, source warning values, and historical ICD codes.
8. The generated RDF graph is reproducible from the committed script and source.
9. Output documentation accurately states its conformance limitations.

These checks provide evidence of RDF syntax, source fidelity, relational integrity and mapping fidelity. They do not certify strict FHIR conformance.

## 7. Unresolved implementation and publication decisions

### W3ID prefix — confirm before public identifier finalization

The Canvas page specifies:

`https://w3id.org/FAIR-course-UT/2025-2026/group{groupnumber}/data#`

However, that page also contains inconsistent examples; the now-removed legacy repository vocabulary previously used:

`https://w3id.org/FAIR-course-UT/2026-2027/group4/ont#`

Do not silently assume either year/prefix or infer that group 4 is currently confirmed. Verify the intended identifier prefix and registered group number.

### Resource identity and local namespaces

Still to settle:

- Deterministic resource URI patterns.
- Local `Identifier.system` URIs.
- Local source CodeSystem reuse/URI policy.
- Representation and canonical URIs of the two project extensions.
- Whether additional local ontology declarations are needed under the course requirements.

These are implementation decisions. Resolve only what is necessary for the agreed RDF output.

### Metadata and publication

The professor has extended Contour to simplify SHACL metadata-schema creation and metadata-record generation, including RDF export.

The team plans to use this capability for metadata work.

FAIR Data Point publication remains operationally difficult. A clarification email has been sent to the professor and a reply is pending.

Do not assume that Contour automatically replaces the FDP publication requirement.

### External integration and report

Identify genuine external linking points and describe possible cross-dataset questions without claiming that integration was executed.

Maintain an evidence-based distinction between baseline FAIR properties and additional FAIRification value.

## 8. Repository documentation and cleanup status (15 October 2026)

The canonical semantic source of truth remains `docs/semantic_model_mapping.md`. Its companion `docs/semantic_mapping_provenance.md` has been **replaced** with a bounded, current FHIR-based decision-provenance record. It is not an independent comprehensive terminology validation.

The superseded files `docs/semantic_model_graph.dot`, `vocab/mimic-icu.ttl`, and `src/explore_data.py` have been **removed from the current repository tree**. Their previous versions remain accessible in Git history, but must not be used as current model or execution inputs.

**README and Codex instructions synchronized (15 October 2026):**

- `README.md` now describes the current five-table resource, canonical model, reproduction workflow, and project status.
- `AGENTS.md` now gives Codex concise operating instructions, the authority hierarchy, frozen semantic-model boundaries, validation checks, and propose → approve → execute change control.

Both replacements were verified in commit `12c3f15101a67ab2674e44a45b657512f027323d`. Consult the current versions, not older copies retained in Git history.

## 9. Next implementation session

The next chat should:

1. Read this handoff and the canonical semantic specification.
2. Inspect the five canonical source tables and current repository state.
3. Resolve the minimum identifier and namespace decisions needed to generate RDF.
4. Present the exact implementation plan and intended new/changed files for approval.
5. After approval, implement the generator and produce an initial Turtle export.
6. Run the acceptance checks and report discrepancies explicitly.
7. Present the verified RDF artifact and reproduction instructions for teammate handoff.

If a genuine semantic contradiction is discovered, stop and surface it rather than silently adjusting the frozen model.

## 10. State-control and evidence rules

Use **propose → approve → execute** for every repository modification.

An implementation plan is not authorization to create or modify files. Any change from the approved specification requires renewed approval.

Distinguish:

- Verified source/repository facts.
- Approved model decisions.
- Proposed implementation choices.
- Deferred questions.
- Unverified assumptions.

Do not treat old assistant-generated drafts or repository history as independent semantic authority.

The immediate success criterion is a **working, checked RDF export**, not a perfect publication infrastructure or a new round of modelling.