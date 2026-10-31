# FAIRification of a MIMIC-IV ICU Vital-Sign Extract — Report draft

Working draft, section by section, following the course report template. The authoritative report is kept separately.

## 1 Introduction

MIMIC-IV Clinical Database Demo v2.2 is an openly available, deidentified 100-patient subset of the MIMIC-IV clinical database, hosted on PhysioNet (Johnson et al., 2023; Pollard et al., 2026). MIMIC-IV contains deidentified electronic health records of patients admitted to the Beth Israel Deaconess Medical Center in Boston. Access to the full database is restricted to credentialed users, whereas the demo provides the same tabular structure at a scale suitable for teaching and preliminary work. The v2.2 archive contains 31 compressed CSV tables: 22 in the hospital module and 9 in the ICU module. It is distributed under the Open Data Commons Open Database License (ODbL) 1.0.

The demo was selected because it retains the realistic clinical data structure and source conventions relevant to ICU research while remaining small enough to FAIRify within the course.

The project resource is a reproducible extract of heart rate, respiratory rate and pulse-oximetry oxygen saturation (SpO2) observations from the first four hours of ICU stays. The four-hour cutoff is an engineering scope boundary, not a clinical claim. Each observation belongs to an ICU stay (stay_id), which is part of a hospital admission (hadm_id) of one patient (subject_id). During a stay, a patient may move through several care units in sequence, and each admission carries its first-ranked billed diagnosis. The extract is derived from seven source tables and organized as five linked tables (Table 1).

**Table 1.** The five tables of the extract.

| Table | Derived from | Records | Columns |
|---|---|---:|---|
| Observations | chartevents, d_items | 2,501 | subject_id, hadm_id, stay_id, charttime, itemid, measurement_label, valuenum, valueuom, warning |
| ICU stays | icustays | 133 | subject_id, hadm_id, stay_id, intime, outtime |
| Care-unit intervals | transfers | 167 | subject_id, hadm_id, stay_id, transfer_id, eventtype, careunit, intime, outtime |
| Hospital admissions | admissions | 121 | subject_id, hadm_id, admittime, dischtime, admission_type |
| First-ranked diagnoses | diagnoses_icd, d_icd_diagnoses | 121 | subject_id, hadm_id, seq_num, icd_code, icd_version, long_title |

Although the source dataset is already well documented, licensed and accessible, much of its meaning is encoded in MIMIC-specific identifiers, text labels, unit strings and relational conventions. For example, itemid 220045 represents heart rate because the MIMIC item dictionary defines it that way; outside the MIMIC ecosystem the code is not self-explanatory. Care units and admission types are likewise recorded as local labels.

The FAIRification therefore represents the extract as RDF aligned with HL7 FHIR R4, links local codes to shared vocabularies (LOINC, UCUM, HL7 terminology, SNOMED CT, ICD) where a defensible mapping exists, and publishes data and metadata under persistent W3IDs, described in a local FAIR Data Point, while preserving the original MIMIC identifiers and values.

## 2 FAIRification planning

### 2.1 FAIRification goals

_To do._

### 2.2 Target resources

_To do._

### 2.3 Target stakeholders

_To do._

### 2.4 Reuse stakeholders

_To do._

### 2.5 FAIRification requirements

_To do._

### 2.6 Semantic types

_To do._

### 2.7 Competency questions

_To do._

## 3 FAIRification process

### 3.1 Initial FAIRness assessment

_To do._

### 3.2 Semantic data model

_To do._

### 3.3 Data triplification

_To do._

### 3.4 Semantic metadata model

_To do._

### 3.5 Metadata and data publication

_To do._

### 3.6 Final FAIRness assessment

_To do._

## 4 Discussion and conclusions

_To do._

## Annexes

### References

Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R. (2023). *MIMIC-IV Clinical Database Demo* (version 2.2). PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/dp1f-ex47

Pollard, T., Moody, B. E., Lehman, L., Gow, B., Fernandes, C., Xie, C., Johnson, A., Mark, R. G., & Heldt, T. (2026). PhysioNet as a global platform for biomedical research. *Nature Health*. https://doi.org/10.1038/s44360-026-00096-z
