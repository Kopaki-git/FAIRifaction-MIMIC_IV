# RDF Serialization — Identifiers, Dialect and Limitations

**Status:** Implemented, first RDF iteration.  
**Decisions recorded:** 15–17 October 2026; W3ID base corrected 21 October 2026.  
**Generator:** `src/generate_rdf.py`  
**Output:** `rdf/mimic_icu_vitals_4h.ttl`  
**Acceptance checks:** `tests/test_rdf.py`

This document records the implementation decisions used to serialize the frozen clinical-semantic model in [`semantic_model_mapping.md`](semantic_model_mapping.md) as RDF. It does not change that model. The model remains the authority for resources, terminology mappings and omissions; this document only fixes identifiers, namespaces and serialization mechanics.

The output is **FHIR R4-aligned RDF**. It is **not** strict FHIR-RDF serialization, and no FHIR instance conformance is claimed.

---

## 1. Reproducing the RDF

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python src/generate_rdf.py          # writes rdf/mimic_icu_vitals_4h.ttl
venv/bin/python -m pytest tests/ -v          # acceptance checks
```

The generator reads only the five canonical tables in `data/derived/mimic_icu_vitals_4h/`, and does not modify them. It stops with an error if a source value falls outside the approved mappings, or if the tables disagree on Patient, admission or ICU-stay links.

---

## 2. Identifier and namespace decisions

| # | Decision | Value |
|---|---|---|
| D1 | W3ID base | `https://w3id.org/FAIR-course-UT/2026/group04/` |
| D2 | Resource IRIs | Hash namespace `https://w3id.org/FAIR-course-UT/2026/group04/data#` |
| D3 | Nested FHIR elements | Blank nodes; IRIs only for the six resource kinds |
| D4 | `Identifier.system` | Reused from MIMIC-FHIR |
| D5 | MIMIC-local CodeSystems | Reused from MIMIC-FHIR |
| D6 | Project extensions | Project URLs under the W3ID base; provisional |
| D7 | Serialization | Simplified FHIR-predicate RDF; timestamps without timezone |

### D1 — W3ID base

The teacher confirmed this namespace for our Canvas group, Group 4. It replaces the base adopted provisionally on 15 October (`2026-2027/group4`).

w3id.org forwards the course namespace to the course's redirect relay, where our rules belong in `rules/FAIR-course-UT/2026/group04/`. Until our rules are submitted there, the IRIs **do not resolve**. Preparing and submitting the rules is a separate workstream.

### D2 — Resource IRI patterns

Prefix `data:` = `https://w3id.org/FAIR-course-UT/2026/group04/data#`. Every IRI is built only from source keys, so the same source always produces the same IRIs.

| Resource | Pattern | Example |
|---|---|---|
| Patient | `data:patient-{subject_id}` | `data:patient-10000032` |
| Hospital Encounter | `data:hospital-encounter-{hadm_id}` | `data:hospital-encounter-29079034` |
| ICU Encounter | `data:icu-encounter-{stay_id}` | `data:icu-encounter-39553978` |
| Condition | `data:condition-{hadm_id}` | `data:condition-29079034` |
| Observation | `data:observation-{stay_id}-{charttime}-{itemid}` | `data:observation-39553978-21800723T141200-220045` |
| Location | `data:location-{slug(careunit)}` | `data:location-medical-intensive-care-unit-micu` |

- In the Observation pattern, `charttime` is written as `YYYYMMDDTHHMMSS`. The source has no observation row identifier, but `(stay_id, charttime, itemid)` is unique across all 2,501 rows.
- One Condition exists per admission, because exactly one first-ranked diagnosis is retained for each.
- `slug` lowercases the verbatim care-unit label, replaces each run of non-alphanumeric characters with `-`, and trims leading or trailing `-`. It yields 9 Location resources.

The MIMIC identifiers inside these IRIs are not treated as global identity. They are also carried explicitly as FHIR `Identifier` values (D4), as model §3.1 requires.

### D3 — Nested elements

The following are blank nodes:
- the datatypes CodeableConcept, Coding, Identifier, Quantity, Period and Extension;
- the backbone elements `Encounter.location` and `Encounter.diagnosis`.

Because of this, reproducibility is checked by comparing graphs, not by comparing the Turtle files byte for byte (§5).

### D4 — Identifier systems (reused from MIMIC-FHIR)

| Source identifier | `Identifier.system` |
|---|---|
| `subject_id` | `http://mimic.mit.edu/fhir/mimic/identifier/patient` |
| `hadm_id` | `http://mimic.mit.edu/fhir/mimic/identifier/encounter-hosp` |
| `stay_id` | `http://mimic.mit.edu/fhir/mimic/identifier/encounter-icu` |

MIMIC assigns these identifiers, not the project. The systems are the required patterns in the published MIMIC-FHIR Implementation Guide (`kindlab.fhir.mimic` 1.3.0, draft). Reusing them keeps the identifiers joinable with MIMIC-FHIR data.

### D5 — MIMIC-local CodeSystems (reused from MIMIC-FHIR)

| Source coding | CodeSystem |
|---|---|
| `itemid` | `http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-chartevents-d-items` |
| raw `icd_code`, `icd_version = 9` | `http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-diagnosis-icd9` |
| raw `icd_code`, `icd_version = 10` | `http://mimic.mit.edu/fhir/mimic/CodeSystem/mimic-diagnosis-icd10` |

The standard codings are unchanged from the model (LOINC, UCUM, HL7, SNOMED CT, `http://hl7.org/fhir/sid/icd-9-cm` and `http://hl7.org/fhir/sid/icd-10-cm`).

### D6 — Project extensions (provisional)

| Extension | Canonical URL | Value |
|---|---|---|
| Observation warning | `https://w3id.org/FAIR-course-UT/2026/group04/fhir/StructureDefinition/observation-mimic-warning` | `valueBoolean`: source `0` → `false`, `1` → `true` |
| Admission type | `https://w3id.org/FAIR-course-UT/2026/group04/fhir/StructureDefinition/encounter-mimic-admission-type` | `valueString`: verbatim `admission_type` |

Their meanings are defined in model §5.6 and §8.1. The warning extension records only that a care provider manually documented a warning. It does not mean the value is abnormal or invalid.

These definitions are **provisional**. No formal FHIR `StructureDefinition` resources exist, and the URLs do not resolve.

---

## 3. Serialization dialect (D7)

The output is **simplified FHIR-predicate RDF**:

- **Predicates are R4 RDF predicate IRIs**, `fhir:{DefiningType}.{path}` with `fhir:` = `http://hl7.org/fhir/`. Examples: `fhir:Observation.status`, `fhir:CodeableConcept.coding`, `fhir:Coding.system`, `fhir:Encounter.location.period`.
- **Extensions use `fhir:DomainResource.extension`**, the predicate R4 defines for them (see §6).
- **Resource types** are given by `rdf:type` (`fhir:Observation`, `fhir:Patient`, `fhir:Encounter`, `fhir:Condition`, `fhir:Location`).
- **References** are direct resource IRIs, e.g. `fhir:Observation.subject data:patient-10000032`.
- **Values are attached directly.** R4 FHIR-RDF machinery is omitted: `fhir:value` wrappers, `fhir:link`, `fhir:index`, `fhir:nodeRole`, `fhir:Resource.id` and concept typing (`a loinc:…`). There is also no `meta.profile`.

**Literal conventions:**

| FHIR type | RDF literal |
|---|---|
| `code`, `string`, identifier values | plain string, e.g. `"final"`, `"220045"`, `"10000032"` |
| `uri` (`Coding.system`, `Identifier.system`, `Quantity.system`, `Extension.url`) | plain string, as in R4 FHIR-RDF (R5 would type it `xsd:anyURI`); query with e.g. `"http://loinc.org"` |
| `decimal` (`valuenum`) | `xsd:decimal`, source lexical form kept (e.g. `91.0`) |
| `boolean` (warning) | `xsd:boolean` |
| `dateTime` | `xsd:dateTime`; source `YYYY-MM-DD HH:MM:SS` with only the space replaced by `T` |
| `positiveInt` (`diagnosis.rank`) | `xsd:positiveInteger` |

**Display text** appears only where the model specifies it: `measurement_label` on the MIMIC item coding, and `long_title` on the source ICD coding.

**Canonical ICD codes** insert the standard decimal point and change nothing else. ICD-9-CM E-codes take the point after the fourth character; all other codes take it after the third, and three-character codes stay undotted (`41401` → `414.01`, `V552` → `V55.2`, `E43` → `E43`, `S0262XA` → `S02.62XA`). The raw code is kept on the source coding.

---

## 4. Output summary

| Item | Count |
|---|---:|
| Observations | 2,501 (LOINC `8867-4` 859, `9279-1` 860, `2708-6` 782 + `59408-5` 782) |
| Patients | 94 |
| Hospital Encounters (`IMP`) | 121 |
| ICU Encounters (`ACUTE`) | 133 |
| `Encounter.location` intervals | 167 |
| Conditions | 121 |
| Locations (care-unit kinds) | 9 |
| Triples | 72,725 |

---

## 5. Verification

`tests/test_rdf.py` implements the acceptance criteria in [`rdf_implementation_handoff.md`](rdf_implementation_handoff.md) §6:

1. **Parsing:** RDFLib and an independent parser (pyoxigraph/Oxigraph) both parse the Turtle file and find the same number of triples.
2. **Counts:** resource and interval counts match the table above.
3. **References:** every Patient, Hospital Encounter, ICU Encounter, Condition and Location reference matches its source row, and every referenced IRI is a typed resource.
4. **Source fidelity:** values (numeric and lexical), source units, charted times, periods, identifiers, verbatim admission types and warning flags all match the source.
5. **Mappings:** checked against tables transcribed separately from the frozen model: LOINC, UCUM, HL7 category, class, priority, care-unit role and diagnosis role codings, SNOMED CT co-codings, and ICD systems.
6. **Edge cases:** SpO₂ dual coding; ICU stays with several care-unit intervals; the single `warning = 1` row; admission types with no standardized priority; Neuro SICU's two role types; historical ICD-10-CM codes `S0262XA` and `T814XXA`, which are kept, not modernized.
7. **Scope:** no `transfer_id` or `eventtype` content, no `meta.profile`, and only `rdf:type` and `fhir:` predicates.
8. **Reproducibility:** two fresh generations and the committed Turtle file must have identical W3C [RDFC-1.0](https://www.w3.org/TR/rdf-canon/) canonical forms, computed with pyoxigraph. Identical canonical forms mean the graphs are isomorphic. A negative control confirms that changing a single literal breaks equality. RDFLib's `rdflib.compare.isomorphic` was tried first but had not finished after 7 minutes on this graph (20,772 blank nodes); RDFC-1.0 takes under a second.

These checks establish RDF syntax, source fidelity, relational integrity and mapping fidelity. They **do not** establish FHIR conformance.

---

## 6. Limitations and open items

- **Not strict FHIR-RDF.** The simplified dialect cannot be validated against the official R4 ShEx schema (`fhir.shex`), whose shapes are closed and require the omitted machinery. ShEx validation was deferred. The official R4 `fhir.shex` also refers to seven `http://hl7.org/fhirpath/System.*` shapes that it never defines, so any future ShEx validation will need a documented local definition of those shapes.
- **Timezones.** FHIR R4 requires a timezone on any `dateTime` that includes a time. MIMIC's timestamps are shifted for deidentification and have no timezone, so none is asserted. This is a known FHIR conformance gap.
- **Provisional extensions.** There are no formal `StructureDefinition`s, and the extension URLs do not resolve.
- **Unsubmitted W3ID redirects.** None of the IRIs resolve yet. The relay rules must cover the `/fhir/StructureDefinition/` paths as well as `/data`, so they need their own rule and test.
- **MIMIC-FHIR dependencies.** The reused identifier systems and CodeSystems come from a *draft* IG (1.3.0) and are not controlled by the project. The MIMIC-FHIR ICD CodeSystem displays may differ from MIMIC `long_title`, which the model requires as the source display. A FHIR validator could flag that as a display mismatch.
- **ICD validity not re-verified.** The canonical ICD codes are format-normalized only. Their historical validity rests on the earlier audit (see [`semantic_mapping_provenance.md`](semantic_mapping_provenance.md)) and was not checked again against CMS/CDC release files.
- **Label discrepancies in the model text.** These do not affect meaning, and the model file was not edited:
  - Model §4 mentions omitting `fhir:v`, which is the **R5** FHIR-RDF wrapper. The R4 equivalent is `fhir:value`, and the simplified dialect omits both.
  - The canonical DAG labels the Observation extension edge `fhir:Observation.extension`. R4 RDF defines the predicate as `fhir:DomainResource.extension`, which is what the output uses. The DAG says its edge labels are display forms.
