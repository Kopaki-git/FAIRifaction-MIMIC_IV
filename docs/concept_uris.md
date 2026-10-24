# Concept URIs

The URIs used in `rdf/mimic_icu_vitals_4h.ttl`, keyed to the labels in [figures/semantic_model_overview.svg](figures/semantic_model_overview.svg). All terms are reused; the project defines no classes or properties of its own. Generated from `src/generate_rdf.py` and checked against the Turtle file.

Prefixes: `fhir:` = `http://hl7.org/fhir/`, `data:` = `https://w3id.org/FAIR-course-UT/2026/group04/data#`.

## Classes

| Diagram box | Class | Count | Note |
|---|---|---:|---|
| Patient | `fhir:Patient` | 94 | |
| Hospital Encounter | `fhir:Encounter` | 121 | `Encounter.class` = `IMP` |
| ICU Encounter | `fhir:Encounter` | 133 | `Encounter.class` = `ACUTE` |
| Observation | `fhir:Observation` | 2,501 | |
| Condition | `fhir:Condition` | 121 | |
| Location | `fhir:Location` | 9 | |

Both encounter boxes are the same FHIR class; the class coding tells them apart.

## Properties

Diagram labels are short forms of these predicates. Bracketed labels on the arrows are nested elements, represented as blank nodes.

| Diagram label | Predicate |
|---|---|
| **Patient** identifier | `fhir:Patient.identifier` |
| **Observation** code | `fhir:Observation.code` |
| value | `fhir:Observation.valueQuantity` |
| effective | `fhir:Observation.effectiveDateTime` |
| category | `fhir:Observation.category` |
| status (not drawn) | `fhir:Observation.status` |
| subject | `fhir:Observation.subject` |
| encounter | `fhir:Observation.encounter` |
| **Encounter** (both) identifier, class, period, subject | `fhir:Encounter.identifier`, `fhir:Encounter.class`, `fhir:Encounter.period`, `fhir:Encounter.subject` |
| status (not drawn) | `fhir:Encounter.status` |
| partOf | `fhir:Encounter.partOf` |
| location [period] | `fhir:Encounter.location` → `fhir:Encounter.location.location`, `fhir:Encounter.location.period` |
| priority | `fhir:Encounter.priority` |
| diagnosis [rank 1, use: billing] | `fhir:Encounter.diagnosis` → `fhir:Encounter.diagnosis.condition`, `fhir:Encounter.diagnosis.rank`, `fhir:Encounter.diagnosis.use` |
| **Condition** code, category, subject, encounter | `fhir:Condition.code`, `fhir:Condition.category`, `fhir:Condition.subject`, `fhir:Condition.encounter` |
| **Location** name, type | `fhir:Location.name`, `fhir:Location.type` |
| mode (not drawn) | `fhir:Location.mode` |
| extension (Observation, Hospital Encounter) | `fhir:DomainResource.extension` |

Datatype properties inside the nested elements:

| Datatype | Predicates |
|---|---|
| CodeableConcept, Coding | `fhir:CodeableConcept.coding`, `fhir:Coding.system`, `fhir:Coding.code`, `fhir:Coding.display` |
| Quantity | `fhir:Quantity.value`, `fhir:Quantity.unit`, `fhir:Quantity.system`, `fhir:Quantity.code` |
| Period | `fhir:Period.start`, `fhir:Period.end` |
| Identifier | `fhir:Identifier.system`, `fhir:Identifier.value` |
| Extension | `fhir:Extension.url`, `fhir:Extension.valueBoolean`, `fhir:Extension.valueString` |

## Terminologies and codes

Codes are recorded as a system URI plus a code (`fhir:Coding.system`, `fhir:Coding.code`), not as concept IRIs.

| Used for | System URI | Codes |
|---|---|---|
| Observation.code | `http://loinc.org` | `8867-4` heart rate; `9279-1` respiratory rate; `2708-6` oxygen saturation, plus `59408-5` oxygen saturation by pulse oximetry for SpO₂ |
| Quantity (units) | `http://unitsofmeasure.org` | `/min` (heart and respiratory rate), `%` (SpO₂) |
| Observation.category | `http://terminology.hl7.org/CodeSystem/observation-category` | `vital-signs` |
| Encounter.class | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | `IMP` hospital stay; `ACUTE` ICU stay |
| Encounter.priority | `http://terminology.hl7.org/CodeSystem/v3-ActPriority` | `EL` elective, `UR` urgent, `EM` emergency; none for observation and same-day admissions |
| Location.type | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` | `ICU`, `NS` neurosurgery unit, `HU` hospital unit, `CCU` coronary care unit |
| Location.type | `http://snomed.info/sct` | `441994008` medical ICU (MICU); `418433008` surgical ICU (SICU) |
| Encounter.diagnosis.use | `http://terminology.hl7.org/CodeSystem/diagnosis-role` | `billing` |
| Condition.category | `http://terminology.hl7.org/CodeSystem/condition-category` | `encounter-diagnosis` |
| Condition.code (canonical) | `http://hl7.org/fhir/sid/icd-9-cm`, `http://hl7.org/fhir/sid/icd-10-cm` | dotted ICD codes, e.g. `414.01` |

Status and mode values (`final`, `finished`, `kind`) are FHIR `code` values with no separate system.

## MIMIC-FHIR systems (source values)

Reused from the MIMIC-FHIR Implementation Guide 1.3.0 (draft), base `http://mimic.mit.edu/fhir/mimic/`:

| Used for | URI (after the base) | Value |
|---|---|---|
| Patient identifier | `identifier/patient` | `subject_id` |
| Hospital Encounter identifier | `identifier/encounter-hosp` | `hadm_id` |
| ICU Encounter identifier | `identifier/encounter-icu` | `stay_id` |
| Observation.code (source) | `CodeSystem/mimic-chartevents-d-items` | `itemid` |
| Condition.code (source) | `CodeSystem/mimic-diagnosis-icd9`, `CodeSystem/mimic-diagnosis-icd10` | raw `icd_code`, e.g. `41401` |

## Project URIs

Under `https://w3id.org/FAIR-course-UT/2026/group04/`:

| URI | Identifies |
|---|---|
| `data#patient-{subject_id}` | Patient |
| `data#hospital-encounter-{hadm_id}` | Hospital Encounter |
| `data#icu-encounter-{stay_id}` | ICU Encounter |
| `data#condition-{hadm_id}` | Condition |
| `data#observation-{stay_id}-{charttime}-{itemid}` | Observation (charttime as `YYYYMMDDTHHMMSS`) |
| `data#location-{careunit slug}` | Location |
| `fhir/StructureDefinition/observation-mimic-warning` | Extension URL: MIMIC warning flag (provisional) |
| `fhir/StructureDefinition/encounter-mimic-admission-type` | Extension URL: verbatim `admission_type` (provisional) |

The extension URLs appear only as `fhir:Extension.url` string values. See `docs/rdf_serialization.md` for the IRI rules (D2) and the extension status (D6).
