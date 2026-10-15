# FAIR MIMIC-IV — Semantic Mapping Provenance

**Status:** Current, bounded decision provenance; not a complete independent terminology-validation dossier.  
**Authoritative model:** [`docs/semantic_model_mapping.md`](semantic_model_mapping.md).  
**Source resource:** MIMIC-IV Clinical Database Demo v2.2, first-four-hour ICU extract in `data/derived/mimic_icu_vitals_4h/`.  
**Last synchronized with model:** 15 October 2026.

## 1. Scope, evidence, and authority

This document records **why the approved semantic mappings were selected**, what source meaning they preserve, and where further verification would be needed. The canonical specification controls the actual model, mapping tables, and deliberate omissions; this document is a provenance companion, not a competing model.

Distinguish three levels of support:

- **Source-grounded:** a property, identifier, or clinical meaning described in the MIMIC data dictionary, source extract, or the relevant HL7/FHIR specification.
- **Approved interpretation:** a modelling policy chosen for this FAIRification, informed by those sources but not necessarily asserted by the sources themselves.
- **Unverified or deferred:** details requiring additional terminology-release checks, FHIR serialization/validation, or publication configuration.

This replacement is derived primarily from the audited canonical model and the sources it cites. **It is not an independent re-audit of every prior choice.** Previous drafts using IAO, SIO, QUDT, SKOS care-unit concepts, and the initial first-careunit-only representation were superseded; their reasoning must not be carried forward as provenance for the FHIR-based model.

## 2. Choice of FHIR R4 as a representation framework

**Approved interpretation.** FHIR R4 supplies standardized clinical structures for `Observation`, `Patient`, `Encounter`, `Location`, and `Condition`. External terminology systems are used in coded fields instead of inventing parallel local classes for the same information structures. This keeps source objects distinguishable from their standardized clinical representation.

**Baseline qualification.** The published MIMIC-FHIR mappings already demonstrate much of the FHIR representation, including observations and encounters. Merely using these resources, assigning `Observation.status = final`, assigning `Encounter.status = finished`, or relating encounters to patients is **not** credited as novel FAIRification. The course-specific contribution must be evaluated relative to MIMIC-IV **and** this existing interoperability work.

**Boundary.** The current DAG is a semantic RDF-oriented specification that intentionally suppresses exact FHIR-RDF serialization details. RDF output is not entitled to a claim of FHIR R4 instance conformance without separate validation.

## 3. Observation identity, time, and warning

- **Source:** each retained `chartevents` measurement row records one charted result. The derived `observations.csv` preserves `subject_id`, `hadm_id`, `stay_id`, `charttime`, `itemid`, `measurement_label`, `valuenum`, `valueuom`, and `warning`.
- **Approved mapping:** one row becomes one `Observation`, referencing the Patient and ICU Encounter. `effectiveDateTime` preserves `charttime`, not an inferred time of data entry or a real, unshifted calendar date.
- **Conversion policy:** `status = final` follows the MIMIC-FHIR conversion approach; it is not a recorded source-field value.
- **Source preservation:** the `warning` integer is represented by a project-defined boolean extension (`0 → false`, `1 → true`), not `Observation.interpretation`. Its meaning must not be inflated to abnormality, incorrectness, or a diagnosis.

**Deferred:** exact local extension canonical URL, resource identifiers, and strict FHIR serialization.

## 4. Measurement coding and units

**Approved MIMIC → LOINC mappings:**

| MIMIC `itemid` | Source measurement | LOINC codings placed in `Observation.code` |
|---|---|---|
| `220045` | Heart Rate | `8867-4` |
| `220210` | Respiratory Rate | `9279-1` |
| `220277` | O2 saturation pulseoxymetry | `2708-6` and `59408-5` |

**Reasoning:** preserve the local `itemid` coding and `measurement_label` beside the external coding rather than replacing source identity. The two SpO₂ codings reflect the generic oxygen-saturation requirement in the R4 Vital Signs profile and the more method-specific pulse-oximetry concept.

**Quantity mapping:** source numeric `valuenum` and verbatim `valueuom` are retained as `Quantity.value` and `Quantity.unit`; `Quantity.system` is `http://unitsofmeasure.org` and `Quantity.code` is `/min` for HR and RR or `%` for SpO₂. The model uses UCUM rather than the prior QUDT-based representation because UCUM fits the selected FHIR Quantity structure, not because QUDT was proven inferior.

**Boundary:** confirm any claim that UCUM normalization is new relative to MIMIC-FHIR before asserting it as a contribution. Source/local code-system URI policy remains deferred.

## 5. Patient and encounter structure

**Source:** `subject_id` identifies MIMIC patients, `hadm_id` hospital admissions, and `stay_id` ICU stays. ICU `intime/outtime` and hospital `admittime/dischtime` delimit different care episodes.

**Approved representation:** one Patient per `subject_id`; one Hospital Encounter per `hadm_id`; one ICU Encounter per `stay_id`. The ICU Encounter references its enclosing Hospital Encounter through `Encounter.partOf`, while Observations reference the ICU Encounter. The source identifiers become local `Identifier.value` entries; they are **not** automatically globally unique RDF identifiers.

Hospital Encounter status/class are `finished` / `IMP`. ICU Encounter status/class are `finished` / `ACUTE`, using the HL7 `v3-ActCode` system. These are approved conversion/classification policies aligned with the MIMIC-FHIR baseline, not observed clinical-status fields or newly discovered FAIR contributions.

## 6. Admission-type semantics

**Source:** MIMIC `admission_type` combines labels conveying urgency and admission pathway. Reusing these directly as the full hospitalization's `Encounter.class` would conflate admission route with encounter setting.

**Approved representation:** hospital Encounter `class = IMP`; preserve the original `admission_type` verbatim through a `valueString` extension. Add `Encounter.priority` with `v3-ActPriority` only where supported by the category's meaning:

| Source `admission_type` | Approved `Encounter.priority` |
|---|---|
| `ELECTIVE` | `EL` |
| `URGENT` | `UR` |
| `EW EMER.` | `EM` |
| `DIRECT EMER.` | `EM` |
| `OBSERVATION ADMIT` | no priority asserted |
| `SURGICAL SAME DAY ADMISSION` | no priority asserted |

**Boundary:** the source values not mapped to priority are intentionally retained without inventing a false urgency equivalence. The extension canonical URL is deferred.

## 7. Time-resolved ICU care-unit context

**Source and preparation:** 167 validated `careunit_intervals.csv` records cover 133 ICU stays and preserve care-unit changes and intervals. The previous `first_careunit`-only representation lost those changes.

**Approved representation:** each interval becomes an `Encounter.location` entry with its own period and a reference to a reusable `Location` resource representing the **kind** of care unit, not a physical bed or independently identified hospital ward. `Location.mode = kind`; `Location.name` retains the original MIMIC label.

**FHIR terminology constraint:** R4 `Location.type` has an *extensible* binding to ServiceDeliveryLocationRoleType. Include the closest applicable code from the bound HL7 role vocabulary even when it is broader than the MIMIC type. Only add a SNOMED coding inside the same type CodeableConcept when the extra specificity was judged directly defensible.

| Source care-unit kind | Approved HL7 v3-RoleCode | Additional SNOMED CT coding |
|---|---|---|
| Medical Intensive Care Unit (MICU) | `ICU` | `441994008` |
| Surgical Intensive Care Unit (SICU) | `ICU` | `418433008` |
| Medical/Surgical Intensive Care Unit (MICU/SICU) | `ICU` | none |
| Trauma SICU (TSICU) | `ICU` | none |
| Neuro Surgical Intensive Care Unit (Neuro SICU) | `ICU` and `NS` (separate `Location.type` entries) | none |
| Neuro Stepdown | `HU` | none |
| Cardiac Vascular Intensive Care Unit (CVICU) | `ICU` | none |
| Coronary Care Unit (CCU) | `CCU` | none |
| Neuro Intermediate | `HU` | none |

**Reasoning and limitation:** broad HL7 classifications are not literal synonyms for the original local categories. The verbatim `Location.name` retains specificity that the standardized layer may lose. No inexact SNOMED relationship is asserted as an equivalent coding merely to map every label. A separate `ConceptMap` for broader relationships is optional and deferred, not an existing deliverable.

**Evidence limitation:** the final HL7 and SNOMED selections are approved canonical modelling choices, **not newly reverified against every release-specific terminology hierarchy** as part of this provenance update.

## 8. First-ranked billed diagnoses

**Source:** `first_ranked_diagnoses.csv` contains one `diagnoses_icd` row with `seq_num = 1` per represented hospital admission. MIMIC describes diagnosis ordering in the billing data; this is not proof of a diagnosis known in the first four ICU hours, a biological cause of admission, or necessarily the primary clinical diagnosis.

**Approved mapping:** Hospital `Encounter.diagnosis` references a `Condition`, with `rank = 1` and `use = billing`; `Condition.category = encounter-diagnosis`, with Patient subject and Hospital Encounter reference.

**Coding:** preserve source `icd_code`, `icd_version`, and `long_title` with a MIMIC-compatible coding and add standard ICD-9-CM or ICD-10-CM coding (`http://hl7.org/fhir/sid/icd-9-cm`, `http://hl7.org/fhir/sid/icd-10-cm`). Insert canonical decimal punctuation without changing original raw codes. Do not assert annual `Coding.version` from an unspecified source release.

The previous audit established historical validity for the selected codes, including `S0262XA` and `T814XXA`; **this cleanup did not independently repeat CMS/CDC release-by-release verification**. Never silently replace historically valid codes with modern successors.

## 9. Deliberate omissions and FAIRification claims

`careunit_intervals.transfer_id` and `eventtype` remain in the canonical input tables but are not modelled as clinical resources or properties. In particular, a transfer event is not automatically promoted to an extra Encounter or physical Location.

The project's intended semantic added value beyond the existing MIMIC-FHIR baseline consists primarily of defensible standard codings, more faithful time-resolved care settings, separation of hospital setting and admission urgency, canonical ICD coding, and explicit billed-diagnosis role/rank. **These are intended improvements, not blanket claims that every mapping is novel or independently validated.**

RDF syntactic validity, source-to-graph completeness, URI resolution, and strict FHIR instance conformance are separate implementation/publication questions and are not established by this provenance document.

## 10. Source basis and verification boundaries

The audited canonical model identifies the following primary references; they remain the source trail for further checking:

- [MIMIC-IV documentation](https://mimic.mit.edu/docs/iv/) — source table semantics, code values, and timing.
- [Published MIMIC-FHIR mappings](https://kind-lab.github.io/mimic-fhir/mimic-fhir-mappings.html) — pre-existing FHIR mapping baseline and conversion policies.
- [FHIR R4 Observation](https://hl7.org/fhir/R4/observation.html), [Vital Signs](https://hl7.org/fhir/R4/observation-vitalsigns.html), [Encounter](https://hl7.org/fhir/R4/encounter.html), [Location](https://hl7.org/fhir/R4/location.html), and [Condition](https://hl7.org/fhir/R4/condition.html) — resource structures and terminology roles.
- [FHIR R4 Extensibility](https://hl7.org/fhir/R4/extensibility.html) and [FHIR R4 RDF](https://hl7.org/fhir/R4/rdf.html) — extensions and serialization constraints.
- [HL7 ServiceDeliveryLocationRoleType](https://terminology.hl7.org/4.0.0/ValueSet-v3-ServiceDeliveryLocationRoleType.html) — role-code binding.
- [LOINC](https://loinc.org/), [UCUM](https://ucum.org/), and historical CMS/CDC ICD releases — external terminology reference bases.

These links identify the evidence trail already used in modelling. **Their presence is not a claim that this 15 October cleanup independently reopened, retrieved, or revalidated all those references.** The authoritative list of the exact approved model elements remains `docs/semantic_model_mapping.md`.
