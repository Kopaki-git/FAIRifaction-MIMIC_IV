# MIMIC-IV Demo FAIRification — Evolving Semantic Model and Vocabulary Mapping

**Status:** Working, version-controlled specification of **approved modelling decisions**; incomplete by design.  
**Last conversational checkpoint:** 2026-10-08, after approval of all nine initial care-unit → SNOMED CT mappings.  
**Dataset:** MIMIC-IV Clinical Database Demo v2.2, first four hours of represented ICU stays.  
**Scope:** Semantic model and vocabulary decisions, **not** an implemented RDF graph, ontology module, or claim of formal conformance.  
**Change policy:** Record only individually approved semantic decisions. Treat proposals and remaining work as explicitly unresolved; require approval before substantive future edits.

This document supersedes the **outdated mapping progress** in the earlier chat-sidebar `FAIR_semantic_model_mapping.md`, but it **does not** replace the original approved conceptual-model handoff, canonical CSV, extraction notebook, or repository's `AGENTS.md`.

## 1. Fixed dataset and interpretation boundaries

| Measure | Value |
|---|---:|
| Clinical observation rows | 2,501 |
| Patients | 94 |
| Hospital admissions | 121 |
| Represented ICU stays | 133 |
| Measurement concepts | 3 |
| Distinct source care-unit types | 9 |
| Distinct source admission types | 6 |

Canonical derived file: `data/derived/mimic_icu_vitals_4h.csv`. Canonical derivation: `notebooks/01_dataset_exploration_and_extraction.ipynb`.

The eleven canonical columns are:

```text
subject_id
hadm_id
admission_type
stay_id
first_careunit
charttime
itemid
measurement_label
valuenum
valueuom
warning
```

- `subject_id`, `hadm_id`, and `stay_id` remain identifiable **as MIMIC-local source identifiers**; the RDF identifier design is pending.
- Individual `ClinicalObservation` resources represent **recorded measurement data** (charted information), not physiological states, acts of measuring, or chart documents.
- `MeasurementConcept` represents a **MIMIC-local reusable type**; its `itemid` and `measurement_label` belong to the concept, not intrinsically to each observation.
- The source `charttime` represents charted observation time, with deidentified timestamps.
- `first_careunit` denotes the **type of the first care unit** of an ICU stay, **not** the location of all observations, an identified physical ward, or necessarily the stay's only care unit.
- `admission_type` classifies the hospital admission, not the observation.
- `warning` is a retained source warning value. Do not silently reinterpret it as invalidity or clinical abnormality.
- The four-hour rule (`charttime >= intime` and `charttime < intime + 4 hours`) is an **extraction/derivation** choice, not a clinical claim; `intime` is not among the eleven canonical output columns.
- No additional Observation → Patient or Observation → Admission direct relation has been approved.

## 2. Evolving semantic model — approved choices and explicit gaps

Names in square brackets identify the selected external class or the still unresolved decision. A bare conceptual relation name with `[predicate unmapped]` is **not** an authorized RDF property.

```text
ClinicalObservation [IAO:0000109 — measurement datum]
    |
    ├── dcterms:type
    │       └──> MeasurementConcept [skos:Concept]
    │              ├── MIMIC itemid
    │              │       [source-identifier property unmapped]
    │              └── MIMIC measurement_label
    │                      [source-label property unmapped]
    |
    ├── belongsToStay [predicate unmapped]
    │       └──> ICUStay [sio:SIO_000006 — process]
    │              |
    │              ├── firstCareUnitType [local predicate planned;
    │              │                       exact URI/definition pending]
    │              │       └──> CareUnitTypeConcept [skos:Concept]
    │              │                └── SNOMED CT mappings: section 4
    │              |
    │              └── sio:SIO_000068 — is part of
    │                      └──> HospitalAdmission
    │                             [sio:SIO_000006 — process]
    │                             |
    │                             ├── hasAdmissionType [predicate unmapped]
    │                             │       └──> AdmissionTypeConcept
    │                             │              [skos:Concept]
    │                             |
    │                             └── sio:SIO_000132 — has participant
    │                                     └──> Patient [class unmapped]
    |
    ├── sio:SIO_000300 — has value
    │       └──> numeric literal (source valuenum)
    |
    ├── sio:SIO_000221 — has unit
    │       └──> reusable QUDT unit resource
    │              ├── Heart Rate       → unit:BEAT-PER-MIN
    │              ├── Respiratory Rate → unit:BREATH-PER-MIN
    │              └── SpO₂             → unit:PERCENT
    |
    ├── project warningFlag [local predicate selected in principle;
    │                        exact namespace/definition pending]
    │       └──> source warning literal
    |
    └── dcterms:date
            └──> typed literal (source charttime)
```

**Important:** `unit:` is the QUDT unit namespace (`http://qudt.org/vocab/unit/`), not `qudt:` (which normally denotes QUDT ontology terms). The model retains the direct observation → unit resource edge, **without** introducing a Quantity/Result node. Source unit strings remain traceable.

## 3. Approved class, relation, and unit selections

### Classes

| Our conceptual element | Approved external type | Meaning/constraint |
|---|---|---|
| ClinicalObservation | [`IAO:0000109` measurement datum](http://purl.obolibrary.org/obo/IAO_0000109) | Information content entity recording measurement output. Directly type each recorded datum; **no** local subclass or equivalent-class axiom approved. |
| MeasurementConcept | [`skos:Concept`](https://www.w3.org/TR/skos-reference/) | Reusable MIMIC-local measurement category. |
| CareUnitTypeConcept | `skos:Concept` | MIMIC-local care-unit category, *not* a location instance. |
| AdmissionTypeConcept | `skos:Concept` | MIMIC-local admission category. |
| ICUStay | [`sio:SIO_000006` process](http://semanticscience.org/resource/SIO_000006) | The **actual time-bounded ICU care episode**, not merely an ICU-stay database record. |
| HospitalAdmission | `sio:SIO_000006` process | The **actual hospitalization episode**, not merely an admission database record. |
| Patient | **Unmapped** | Individual participating in the admission; source `subject_id` preserved. |

### Relations and literals

| Conceptual relationship | Approved RDF property / decision | Boundary |
|---|---|---|
| ClinicalObservation → MeasurementConcept | [`dcterms:type`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/type/) | Classify the charted measurement datum by its MIMIC-local reusable measurement type; not `dcterms:subject` or a link to an actual physiological quality. |
| ClinicalObservation → numeric value | [`sio:SIO_000300` has value](http://semanticscience.org/resource/SIO_000300) | Direct numeric literal; no Quantity node. |
| ClinicalObservation → unit | [`sio:SIO_000221` has unit](http://semanticscience.org/resource/SIO_000221) | Direct resource link to standard QUDT unit. |
| ClinicalObservation → chart time | [`dcterms:date`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/terms/date/) | Charted time as typed literal, not inferred result publication or provenance generation time. |
| ClinicalObservation → warning flag | **Local warning-flag property** | Preserve source warning literally. Provisional shorthand `mimic:warningFlag` appeared in discussion; its actual project namespace and formal definition remain undecided. |
| ICUStay → HospitalAdmission | [`sio:SIO_000068` is part of](http://semanticscience.org/resource/SIO_000068) | One care episode is part of its encompassing hospitalization episode. |
| HospitalAdmission → Patient | [`sio:SIO_000132` has participant](http://semanticscience.org/resource/SIO_000132) | Patient participates in the hospitalization; avoids vague source-level `belongsToPatient` meaning. |
| ICUStay → first care-unit type | **Direct link; local predicate planned** | Preserve the `first` semantics and connect directly to a `skos:Concept`; property IRI/definition not finalized. |
| ClinicalObservation → ICUStay | **Unmapped** | Observation is information recorded *in the context* of a stay. Do **not** substitute physical part-of or participation without justification. |
| HospitalAdmission → AdmissionTypeConcept | **Unmapped** | `dcterms:type` is a discussed candidate, not yet approved. |

**Deliberate rejected commitments:** FHIR `Observation`/`Encounter` resource modelling and related reference wrappers; IAO scalar measurement datum `IAO:0000032` with its more restrictive unit-label structure; SPHN `Location`/pooled or unidentified physical-ward resources for `first_careunit`; SPHN's measurement-process/result/quantity graph in place of our datum-centred graph. SPHN remains eligible for **selective term reuse** when independently justified, with no project-level SPHN conformance claim.

### Unit normalization

| MIMIC measurement | `itemid` | Source label | Source unit text | Approved QUDT unit |
|---|---:|---|---|---|
| Heart Rate | 220045 | Heart Rate | `bpm` | [`unit:BEAT-PER-MIN`](http://qudt.org/vocab/unit/BEAT-PER-MIN) |
| Respiratory Rate | 220210 | Respiratory Rate | `insp/min` | [`unit:BREATH-PER-MIN`](http://qudt.org/vocab/unit/BREATH-PER-MIN) |
| SpO₂ | 220277 | O2 saturation pulseoxymetry | `%` | [`unit:PERCENT`](http://qudt.org/vocab/unit/PERCENT) |

These are **source-specific normalization decisions**. They do not mean replacing original values/units or making every possible MIMIC unit string interchangeable with the chosen QUDT resource. The reusable measurement types have **not yet** been aligned with external physiological measurement terminology (e.g., LOINC or SNOMED).

## 4. Approved care-unit-type terminology mappings (all nine)

Each source value denotes a **MIMIC-local `skos:Concept`**. The expressions `MIMIC:MICU`, etc., are **illustrative labels**, not approved permanent local concept IRIs. Standard mapping predicates are used to align these local concepts with SNOMED CT Environment concepts; the source concepts remain separate.

| MIMIC source care-unit category | Mapping | SNOMED CT target | Meaning and caution |
|---|---|---|---|
| Medical Intensive Care Unit (MICU) | **`skos:exactMatch`** | [`441994008` — Medical intensive care unit](http://snomed.info/id/441994008) | High-confidence corresponding medical ICU category; approved as interchangeability for concept retrieval. |
| Surgical Intensive Care Unit (SICU) | **`skos:exactMatch`** | [`418433008` — Surgical intensive care unit](http://snomed.info/id/418433008) | High-confidence corresponding surgical ICU category. |
| Medical/Surgical Intensive Care Unit (MICU/SICU) | **`skos:broadMatch`** | [`309904001` — Intensive care unit](http://snomed.info/id/309904001) | Loses combined medical/surgical specialty. |
| Trauma SICU (TSICU) | **`skos:broadMatch`** | [`418433008` — Surgical intensive care unit](http://snomed.info/id/418433008) | Loses trauma specialty. |
| Neuro Surgical ICU | **`skos:broadMatch`** | [`309909006` — Neurological intensive care unit](http://snomed.info/id/309909006) | Loses surgical specialty. |
| Neuro Stepdown | **`skos:broadMatch`** | [`419590001` — Stepdown unit](http://snomed.info/id/419590001) | Loses neurological specialty, retains the stepdown setting. |
| Cardiac Vascular ICU (CVICU) | **`skos:broadMatch`** | [`309904001` — Intensive care unit](http://snomed.info/id/309904001) | Avoids incorrectly reducing combined cardiac/vascular scope to only cardiac. |
| Coronary Care Unit (CCU) | **`skos:broadMatch`** | [`309907008` — Cardiac intensive care unit](http://snomed.info/id/309907008) | Broadens from coronary to cardiac critical care. |
| Neuro Intermediate | **`skos:broadMatch`** | [`397771005` — High dependency unit](http://snomed.info/id/397771005) | Proposed as general intermediate/high-dependency care setting; exact institutional boundaries unverified. |

Mapping count: **2 `skos:exactMatch` + 7 `skos:broadMatch` = 9 approved design decisions.**

**Epistemic status:** The mappings above were approved after comparison of MIMIC care-unit labels/meaning, healthcare terminology references, and the SKOS mapping-strength definitions. They are **not** asserted to have passed release-specific SNOMED subsumption verification, national-extension review, or automated terminology validation. That remains a final audit requirement. In particular, retain the important clinical distinctions in the original MIMIC-local concepts even when a SNOMED target is broader.

## 5. Vocabulary selection and modelling rules (approved)

1. Search established vocabularies for **classes, object/data predicates, units, and controlled concepts** before introducing project-local terms.
2. Evaluate **definitions, modelled entities, domain/range, ontology hierarchy, additional logical commitments, maintained identifiers, and use-case fit**—never label similarity alone.
3. Prefer the **least restrictive established class that faithfully describes the intended thing**. More specificity needs concrete payoff for modelling, querying, reasoning, or interoperability.
4. Preserve MIMIC-local code identity and original wording; add external links **without** silently substituting terminology.
5. Distinguish `skos:exactMatch`, `skos:closeMatch`, `skos:broadMatch`, and other mapping strengths based on evidence; do not assert `owl:sameAs` casually.
6. Use **multiple compatible vocabularies** when useful rather than forcing the entire project into FHIR, SPHN, or any other single standard.
7. Treat graph centrality as distinct from ontological superclass/part-whole claims.
8. Stop vocabulary searching at **defensible sufficiency**, not fictitious global optimality; reopen when new evidence makes the decision materially uncertain.
9. Retain the eleven-field source extract and the derivation rule. Do not add hospital location identities, transfer episodes, patient demographics, diagnoses, medications, etc. solely to satisfy an external schema.

## 6. Remaining decisions, tests, and implementation work

**Unresolved semantic choices** (not permission to auto-complete or rewrite them):

- Choose the external type for `Patient`.
- Map the contextual `ClinicalObservation → ICUStay` relation without claiming unsupported measurement participation, physical parthood, or provenance.
- Define and mint the local `firstCareUnitType` property **if** no suitable established predicate can express the source meaning; retain the direct SKOS concept link.
- Select a property for `HospitalAdmission → AdmissionTypeConcept`; `dcterms:type` is a candidate only.
- Choose external terminology mappings for the three MIMIC `MeasurementConcept` values (source `itemid` 220045/220210/220277).
- Resolve the six source admission-type concepts and any suitable external terminology mappings.
- Map source identifiers, labels, source unit-string retention, and local warning property in explicit RDF; determine stable namespace prefixes and full IRIs.
- Design RDF URIs for patient, admission, stay, local measurement concepts, local care-unit/admission-type concepts and each individual observation (no source observation ID).
- Add documented dataset derivation/provenance metadata, machine-actionable metadata, and validation/SHACL as separate downstream work.
- Audit namespace consistency and exact predicate definitions/domains/ranges; verify SNOMED concept IDs, Environment hierarchy and release-specific status; test source-to-RDF preservation and competency questions.
- No RDF transformation/export or SHACL validation has yet been implemented or claimed here.

**Current next modelling gate:** the `ClinicalObservation → ICUStay` contextual predicate.

## 7. Primary references

- [MIMIC-IV Demo v2.2 on PhysioNet](https://physionet.org/content/mimic-iv-demo/2.2/)
- [MIMIC-IV ICU stay documentation](https://mimic.mit.edu/docs/iv/modules/icu/icustays.html)
- [MIMIC-IV chart events documentation](https://mimic.mit.edu/docs/iv/modules/icu/chartevents.html)
- [MIMIC-IV hospital admissions documentation](https://mimic.mit.edu/docs/iv/modules/hosp/admissions.html)
- [Information Artifact Ontology source](https://github.com/information-artifact-ontology/IAO/blob/master/src/ontology/iao-edit.owl)
- [Semanticscience Integrated Ontology](https://github.com/MaastrichtU-IDS/semanticscience)
- [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/)
- [Dublin Core DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
- [QUDT unit vocabulary](https://qudt.org/)
- [SNOMED CT concept identifiers](https://browser.ihtsdotools.org/)
- [SPHN Semantic Framework](https://sphn.ch/)

**Change-control boundary:** Do not edit this file merely because a candidate looks promising. First inspect current state, propose an exact and traceable change, obtain approval, and only then commit that approved change.
