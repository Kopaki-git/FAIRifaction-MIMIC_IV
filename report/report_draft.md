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

MIMIC-IV is already FAIR at the metadata level. It has a DataCite DOI, a stated licence, documentation and open access over HTTPS. A FHIR mapping of MIMIC (MIMIC-FHIR) also already exists. The goals therefore address the data, and conversion to FHIR is not in itself claimed as a contribution. The aim is a resource that is easier to interpret, trace, combine and reuse, without losing the source-specific meaning supplied by MIMIC.

1. **Machine-actionable representation.** Represent the extract in RDF using the structures of an established clinical information model, HL7 FHIR R4. This replaces columns whose meaning is defined only in documentation. (I1)
2. **Shared vocabularies beside local codes.** Link MIMIC-local codes and labels to shared vocabularies wherever a defensible mapping exists: LOINC for measurements, UCUM for units, HL7 terminology for encounter class, admission priority and care-unit type, SNOMED CT for two care units, and canonical ICD-9-CM and ICD-10-CM codes for diagnoses. The original MIMIC values are kept next to the standard ones, and no mapping is forced where none is defensible. For ICU data, MIMIC-FHIR uses MIMIC-local code systems, and its implementation guide lists both the mapping to standard terminology and the adoption of the canonical ICD code systems as future work (KinD Lab, 2024). (I2, R1.3)
3. **Explicit clinical distinctions.** Make three distinctions machine-readable that MIMIC leaves implicit and MIMIC-FHIR does not represent:
    - the sequence of care units within an ICU stay, each with its own time interval, where MIMIC-FHIR assigns the ICU encounter its first care unit for the whole stay;
    - the class of a hospital admission, separated from its urgency, where MIMIC-FHIR places the source admission type in both;
    - the rank and billing role of the first-ranked diagnosis, so that it reads as a billing diagnosis rather than a presumed cause of admission. (I3, R1)
4. **Persistent identifiers.** Give the dataset, each of its distributions and every represented resource a globally unique, persistent and resolvable identifier. (F1, A1)
5. **Rich, findable metadata.** Describe the dataset and its distributions with machine-readable metadata, including licence and provenance, validated against a metadata schema and published in a FAIR Data Point. (F2, F3, F4, R1.1, R1.2)
6. **Reproducible derivation.** Make the path from the source release to the FAIRified resource repeatable and checkable. (R1.2)

### 2.2 Target resources

1. **The data:** the five-table extract described in Section 1, to be represented as an RDF graph.
2. **The metadata:** a description of the extract as a dataset with three distributions:
    - the source release;
    - the extract as CSV tables;
    - the extract as RDF.

The rest of the MIMIC-IV Demo is out of scope.

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

KinD Lab. (2024). *MIMIC Implementation Guide* (version 1.3.0, draft). HL7 FHIR R4. https://kind-lab.github.io/mimic-fhir/

Pollard, T., Moody, B. E., Lehman, L., Gow, B., Fernandes, C., Xie, C., Johnson, A., Mark, R. G., & Heldt, T. (2026). PhysioNet as a global platform for biomedical research. *Nature Health*. https://doi.org/10.1038/s44360-026-00096-z
