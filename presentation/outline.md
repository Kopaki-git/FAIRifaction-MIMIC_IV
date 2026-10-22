# Presentation outline — 26 October 2026

Working template, structured by the six topics the Canvas project page requires, in its order.

**Canvas requirements:**
- The presentation is split evenly between the two members.
- Questions assess each member's participation and their knowledge of the course topics.

**Each section lists:**
- **Message:** the one sentence the audience should remember.
- **Show:** what goes on the slides.
- **Sources:** where the content comes from.
- **Status:** whether it can be presented as done.
- **Presenter.**

## 0. To settle first

- [ ] Duration. Not on the project page yet; this sets the time per section.
- [ ] Presenter split. Suggestion: each member presents the parts they built, since the questions test participation.
  - Harveer: data preparation and semantic model (sections 3–4).
  - Teammate: metadata schema (section 5).
  - Split the rest: dataset, planning, FAIRness improvements (sections 1, 2, 6).
- [ ] Stakeholders and reuse scenarios (section 2). **Not documented anywhere in the repo.** Check whether they exist from an earlier assignment or still need writing.
- [ ] Live SPARQL demo or screenshots.

## Wording rules

| Say | Don't say |
|---|---|
| FHIR R4-**aligned** RDF | FHIR conformant / valid FHIR |
| Identifiers **designed** for W3ID resolution | Resolvable identifiers (relay not submitted yet) |
| Metadata and FDP publication **in progress** | Published in an FDP |
| Improvements **over** MIMIC-IV and MIMIC-FHIR in specific areas | MIMIC-IV was not FAIR / FHIR conversion is our contribution |

---

## Title slide

- **Show:** project title, Group 04, both names, course.

## 1. The chosen dataset

- **Message:** an open, well-documented ICU dataset, whose meaning is still largely in local codes and free-text labels.
- **Show:**
  - **What it is about:** de-identified ICU and hospital data from Beth Israel Deaconess Medical Center. Our scope is vital signs (heart rate, respiratory rate, SpO₂) in the first 4 hours of ICU stays.
  - **Where we found it:** PhysioNet, MIMIC-IV Clinical Database Demo v2.2, DOI 10.13026/dp1f-ex47, open access under ODbL 1.0.
  - **Current format:** gzipped CSV tables (`.csv.gz`). We use 7 of them, and our extract is 5 linked CSVs.
  - **Existence of metadata:**
    - PhysioNet project page, DOI, documentation and versioning.
    - Data dictionaries inside the data (`d_items`, `d_icd_diagnoses`).
    - The MIMIC-FHIR mappings as an existing interoperability layer.
    - Little machine-actionable semantics at column level: itemids, care-unit labels and admission-type strings.
- **Sources:** README "Project resource"; model §1–2; PhysioNet page.
- **Status:** done.
- **Presenter:**

## 2. FAIRification planning

- **Message:** a bounded scope chosen for specific semantic gaps, not a whole-database conversion.
- **Show:**
  - **Stakeholders:** _(fill in; not documented in the repo)_
  - **Reuse scenarios:** _(fill in)_. The SPARQL queries suggest some: cross-dataset vital-sign analysis by LOINC, outcome or diagnosis cohorts, care-unit comparisons.
  - **Scope decisions:** the 4-hour window as an engineering choice, three vital signs, first-ranked diagnosis.
  - **Baseline:** what is already FAIR (MIMIC-IV, MIMIC-FHIR), so the improvements are measured against it.
- **Sources:** README "FAIRification claims and limitations"; model §1, §3.5.
- **Status:** scope done; stakeholders and scenarios **to write**.
- **Presenter:**

## 3. Data preparation

- **Message:** a reproducible extraction that reshapes the data without altering source values.
- **Show:**
  - **Ignored:** everything outside the three itemids and the 4-hour window. `transfer_id` and `eventtype` are kept in the CSVs but left out of the graph (model §11).
  - **Split / derived:** a single `first_careunit` becomes time-bounded care-unit intervals (167 intervals for 133 stays).
  - **Merged / linked:** observation ↔ ICU stay ↔ admission ↔ patient; first-ranked diagnosis joined to its ICD title.
  - **Reconciled:**
    - ICD codes dotted into canonical form, raw code kept;
    - admission types mapped to an HL7 priority only where defensible;
    - care-unit labels mapped to HL7 roles, plus SNOMED for two units.
  - **Format conversion:** CSV → RDF Turtle via a Python/RDFLib script, with deterministic IRIs. Unmapped values stop the run.
  - **Checks:**
    - relational integrity in the notebook;
    - 27 RDF tests: fidelity and reproducibility (RDFC-1.0), 72,725 triples.
- **Sources:** notebook §§2–9; model §2.1, §8–11; `src/generate_rdf.py`; `docs/rdf_serialization.md` §§2–5.
- **Status:** done.
- **Presenter:**

## 4. Semantic data model

- **Message:** FHIR R4 structure plus standard terminologies, keeping MIMIC values next to standard codes.
- **Show:**
  - **Diagram:** Patient, Hospital Encounter, ICU Encounter, Location, Observation, Condition. It also goes in the report.
  - **Terminologies:** LOINC, UCUM, HL7, SNOMED CT, ICD-9/10-CM.
  - **Key decisions**, pick 2–3:
    - time-resolved care-unit history (§9)
    - admission class separated from urgency (§8)
    - billed diagnosis, not presumed cause (§10)
    - qualified, broader-not-equivalent care-unit mappings (§9.2–9.3)
    - warning flag without implied abnormality (§5.6)
  - **Own terms:** two provisional extensions (warning, admission type) under our W3ID base.
- **Sources:** model §4 (DAG), §4.1 (backbone), §§5–10; provenance §§2–8.
- **Status:** done. Whether an RDF/OWL file is required is **awaiting the professor**.
- **Presenter:**

## 5. Metadata schema

- **Message:** DCAT metadata for the dataset and its distributions, constrained by our SHACL shapes.
- **Show:**
  - **Shapes:** Dataset, Distribution, Organization, and the properties they require.
  - **Dataset vs distribution:** the abstract dataset vs the CSV and RDF forms.
  - **Planned:** licence, provenance (`prov:wasDerivedFrom` the Demo) and access rights.
  - **Publication:** via a FAIR Data Point.
- **Sources:** `metadata/`; decisions in progress (licence ODbL, access PUBLIC, creator/publisher Group 04).
- **Status:** **in progress.** The original-distribution framing and the schema file split are pending; present the design, not final records.
- **Presenter:**

## 6. FAIRness improvements

- **Message:** concrete gains, each tied to a FAIR principle and shown, not asserted.
- **Show:** a table of principle → before → after. Candidates:
  - **F1:** row-index or local IDs → persistent W3IDs under `…/2026/group04/data#` (designed; relay pending).
  - **I1/I2:** local itemids and labels → LOINC, UCUM, HL7, SNOMED, ICD codes beside the source values.
  - **I3:** links between observations, stays, admissions and diagnoses explicit in RDF.
  - **R1.1:** licence stated explicitly (ODbL).
  - **R1.2:** provenance to the Demo DOI; reproducible generation.
  - **Before/after demo:** one question run on the non-FHIR graph and on the FHIR graph, e.g. observations by LOINC code (`sparql/fhir/02…`).
- **Sources:** `sparql/`; README "FAIRification claims"; model §3.5.
- **Status:** RDF side done; F1 resolution and metadata pending.
- **Presenter:**

## Closing: limitations (optional slide or Q&A backup)

- Not strict FHIR-RDF; no ShEx validation.
- Timestamps without timezone.
- Provisional extensions.
- Draft MIMIC-FHIR systems.
- ICD codes format-normalized only.
- **Pending:** redirects, FDP, the original-distribution and ontology questions.
- **Source:** `docs/rdf_serialization.md` §6.

---

## Q&A preparation

Questions will test each member on their own work and on the course. Both members should be able to answer:

- What F1, A1, I2 and R1.2 mean, and where this project meets them.
- Why W3ID; what a 303 redirect does; why hash IRIs (`data#…`).
- Dataset vs distribution in DCAT; what SHACL validates and what it does not.
- What an FDP is for.
- Why FHIR, and why "aligned" and not "conformant".
- Why LOINC and UCUM next to the MIMIC codes instead of replacing them.

## Report sections that follow from this

| Section | Report section |
|---|---|
| 1–2 | Dataset, FAIR baseline, planning |
| 3 | Data preparation and transformation |
| 4 | Semantic model and decisions, with the diagram |
| 5 | Metadata schema and publication (finish after the professor replies) |
| 6 | FAIRness evaluation |
| Closing | Limitations |
