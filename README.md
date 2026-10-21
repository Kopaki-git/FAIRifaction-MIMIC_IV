# FAIRification of a MIMIC-IV ICU Vital-Sign Extract

A FAIR Data Engineering course project at the University of Twente, based on the **MIMIC-IV Clinical Database Demo v2.2**.

The project takes a reproducible, bounded collection of ICU vital-sign observations and related clinical context, then develops a semantically interoperable RDF representation.

MIMIC-IV already provides substantial FAIR infrastructure, including documentation, versioning, distribution and provenance. Our objective is not to characterize the original as non-FAIR, but to demonstrate specific, defensible improvements in machine-actionable semantic interoperability.

## Project resource

The original, still-unFAIRified project resource consists of five linked CSV tables in:

`data/derived/mimic_icu_vitals_4h/`

| File | Rows | Represents |
|---|---:|---|
| `observations.csv` | 2,501 | Charted heart rate, respiratory rate and SpO₂ measurements |
| `icu_stays.csv` | 133 | Represented ICU stays |
| `careunit_intervals.csv` | 167 | Time-bounded ICU care-unit intervals |
| `hospital_admissions.csv` | 121 | Corresponding hospital admissions |
| `first_ranked_diagnoses.csv` | 121 | First-ranked billed diagnosis per admission |

The resource covers **94 patients, 121 hospital admissions and 133 ICU stays**.

The selection includes observations in the interval `[ICU intime, ICU intime + 4 hours)`, for these MIMIC identifiers:

| MIMIC `itemid` | Measurement | Observations |
|---|---|---:|
| `220045` | Heart rate | 859 |
| `220210` | Respiratory rate | 860 |
| `220277` | Pulse-oximetry SpO₂ | 782 |

The four-hour window is an engineering scope decision, not a clinical threshold. All represented ICU stays have observations of all three measurement types.

## Reproducing the original resource

The authoritative extraction is:

`notebooks/01_dataset_exploration_and_extraction.ipynb`

It uses seven upstream tables from the open MIMIC-IV Demo v2.2 release:

- ICU: `chartevents.csv.gz`, `icustays.csv.gz`, `d_items.csv.gz`
- Hospital: `admissions.csv.gz`, `transfers.csv.gz`, `diagnoses_icd.csv.gz`, `d_icd_diagnoses.csv.gz`

Place the upstream files beneath `data/icu/` and `data/hosp/`, preserving those filenames.

Install the notebook dependencies:

```bash
python3 -m pip install pandas jupyter
```

Open the notebook from within the repository and use **Restart Kernel and Run All**. Its transformations, validation checks and final export write the five tables under `data/derived/mimic_icu_vitals_4h/`.

The original downloaded MIMIC files are deliberately excluded from Git. The five derived CSVs are committed and remain unchanged as the project's pre-FAIRification reference.

MIMIC timestamps are shifted for deidentification. They preserve relevant temporal relationships but must not be interpreted as real-world calendar dates.

## Generating the RDF

The RDF export is generated from the five derived tables by a Python/RDFLib script:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python src/generate_rdf.py          # writes rdf/mimic_icu_vitals_4h.ttl
venv/bin/python -m pytest tests/ -v          # acceptance checks
```

The identifier decisions, serialization rules, verification scope and limitations are documented in [`docs/rdf_serialization.md`](docs/rdf_serialization.md).

## Canonical semantic model

The approved clinical-semantic specification is:

**[`docs/semantic_model_mapping.md`](docs/semantic_model_mapping.md)**

It is the single source of truth for the model, including its full RDF-oriented DAG, simplified backbone, mappings and exclusions.

The design uses FHIR R4 clinical structures for `Patient`, `Observation`, `Encounter`, `Location` and `Condition`, with established terminology where applicable.

It preserves source identifiers and values while adding appropriately qualified representations using LOINC, UCUM, HL7 terminology, selected SNOMED CT concepts and canonical ICD coding.

Notable features include:

- Observations explicitly linked to patients and ICU encounters.
- A hospital/ICU encounter hierarchy.
- Time-resolved ICU care-unit intervals rather than a single first-careunit label.
- Qualified mappings for care-unit types.
- Hospital admission class separated from admission urgency.
- First-ranked diagnoses represented as billed encounter diagnoses rather than presumed clinical causes.

The detailed mapping rationale and its evidence limitations are documented in [`docs/semantic_mapping_provenance.md`](docs/semantic_mapping_provenance.md).

## FAIRification claims and limitations

The comparison baseline includes both the original MIMIC-IV data and the existing [MIMIC-FHIR mappings](https://kind-lab.github.io/mimic-fhir/mimic-fhir-mappings.html).

Simply representing MIMIC entities as FHIR resources is not, by itself, a novel interoperability contribution.

The project instead seeks to demonstrate concrete improvements in care-setting history, terminology alignment, admission classification and diagnosis representation, while making the bounded resource available through RDF and accompanying FAIR publication infrastructure.

The canonical model is FHIR-aligned. **Strict FHIR-RDF serialization and FHIR instance conformance must not be claimed without separate verification.**

## Current implementation status

As of 17 October 2026:

- Canonical source extraction and validation: **completed**.
- Clinical-semantic model and terminology choices: **audited and frozen**.
- Current semantic provenance documentation: **available**, with explicit evidence limitations.
- Identifier and namespace decisions: **resolved**; the W3ID base `https://w3id.org/FAIR-course-UT/2026/group04/` is confirmed by the teacher.
- Executable RDF transformation (Python/RDFLib) and Turtle export: **implemented**, `rdf/mimic_icu_vitals_4h.ttl`.
- RDF acceptance checks: **implemented** in `tests/test_rdf.py`. They check syntax, source fidelity, relational integrity, mapping fidelity and reproducibility, not FHIR conformance.
- W3ID redirect registration and publication infrastructure: **pending**.
- Metadata and FAIR Data Point work: **in progress or pending**, coordinated separately.

The output is FHIR R4-aligned, simplified FHIR-predicate RDF, not strict FHIR-RDF. Its decisions and limitations are recorded in [`docs/rdf_serialization.md`](docs/rdf_serialization.md). The original acceptance criteria are in [`docs/rdf_implementation_handoff.md`](docs/rdf_implementation_handoff.md).

## Repository structure

```text
.
├── AGENTS.md
├── README.md
├── data/
│   └── derived/
│       └── mimic_icu_vitals_4h/
│           ├── observations.csv
│           ├── icu_stays.csv
│           ├── careunit_intervals.csv
│           ├── hospital_admissions.csv
│           └── first_ranked_diagnoses.csv
├── docs/
│   ├── semantic_model_mapping.md
│   ├── semantic_mapping_provenance.md
│   ├── rdf_implementation_handoff.md
│   └── rdf_serialization.md
├── notebooks/
│   └── 01_dataset_exploration_and_extraction.ipynb
├── rdf/
│   └── mimic_icu_vitals_4h.ttl
├── requirements.txt
├── src/
│   └── generate_rdf.py
└── tests/
    └── test_rdf.py
```

## Source, licensing and attribution

Source dataset: [MIMIC-IV Clinical Database Demo v2.2 on PhysioNet](https://physionet.org/content/mimic-iv-demo/2.2/).

Consult the source release for its licensing, citation and attribution requirements before redistributing or republishing derived resources.

Changes to the extraction, clinical-semantic model or publication assumptions should be documented explicitly. Do not silently alter the original derived tables or reinterpret source variables.
