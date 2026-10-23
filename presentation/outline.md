# Presentation outline — 26 October 2026

Working template, structured by the six topics the Canvas project page requires, in its order. Updated 23 October 2026 to the state after the professor's reply, the relay going live and the metadata record being completed.

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

- [x] Duration: **10 minutes**, ±1 minute, so about 5 minutes per member. Suggested timing:

  | Section | Minutes |
  |---|---|
  | Title + 1. Dataset | 1 |
  | 2. Planning | 1.5 |
  | 3. Data preparation | 1.5 |
  | 4. Semantic model | 2 |
  | 5. Metadata and publication | 2 |
  | 6. FAIRness improvements | 2 |

  At this length, keep limitations as Q&A backup rather than a slide, and use screenshots, not a live demo.
- [ ] Presenter split. Suggestion: each member presents the parts they built, since the questions test participation.
  - Harveer: data preparation and semantic model (sections 3–4).
  - Teammate: metadata schema and publication (section 5).
  - Split the rest: dataset, planning, FAIRness improvements (sections 1, 2, 6).
- [ ] Stakeholders and reuse scenarios (section 2). Drafted outside the repo; bring them into the slides.
- [ ] Model diagram (section 4). Not made yet; also needed for the report.
- [ ] SPARQL screenshots for section 6 (a live demo is risky in 10 minutes).

## Wording rules

| Say | Don't say |
|---|---|
| FHIR R4-**aligned** RDF | FHIR conformant / valid FHIR |
| Persistent, **resolvable** W3IDs; `data#…` IRIs resolve to the Turtle file | Every IRI resolves to its own page (a browser lands on the file or folder, not the resource) |
| Metadata record **live via W3ID**; FDP publication **in progress** | Published in an FDP (until it is) |
| FAIRness **self-assessed** with the RDA FAIR Data Maturity Model | Evaluated / certified FAIR |
| Improvements **over** MIMIC-IV and MIMIC-FHIR in specific areas | MIMIC-IV was not FAIR / FHIR conversion is our contribution |
| The non-FHIR graph is our **comparison** model | Published second dataset |

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
    - PhysioNet project page, DOI with a DataCite record, schema.org JSON-LD, documentation and versioning.
    - Data dictionaries inside the data (`d_items`, `d_icd_diagnoses`).
    - The MIMIC-FHIR mappings as an existing interoperability layer.
    - Little machine-actionable semantics at column level: itemids, care-unit labels and admission-type strings.
- **Sources:** README "Project resource"; model §1–2; PhysioNet page; `docs/fair_assessment.md` "Original".
- **Status:** done.
- **Presenter:**

## 2. FAIRification planning

- **Message:** a bounded scope chosen for specific semantic gaps, not a whole-database conversion.
- **Show:**
  - **Stakeholders:** _(from the draft)_
  - **Reuse scenarios:** _(from the draft)_. The SPARQL queries in `sparql/fhir/` answer three of them as competency questions:
    - heart rate by first-ranked diagnosis;
    - observations per LOINC code (comparable across datasets);
    - warning-flagged observations with patient, stay and care-unit context.
  - **Scope decisions:** the 4-hour window as an engineering choice, three vital signs, first-ranked diagnosis.
  - **Baseline:** the original is already FAIR at the metadata level (DOI, DataCite, licence, open HTTPS). Its gaps are in the data. Improvements are measured against that.
- **Sources:** README "FAIRification claims and limitations"; model §1, §3.5; `docs/fair_assessment.md` summary.
- **Status:** scope and baseline done; stakeholders and scenarios to transfer from the draft.
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
    - 27 RDF tests: parsing, counts, references, fidelity, codings, edge cases and reproducibility (RDFC-1.0); 72,725 triples;
    - 2 tests for the CSV distribution ZIP: identical to the CSVs, and rebuilt byte for byte.
- **Sources:** notebook §§2–9; model §2.1, §8–11; `src/generate_rdf.py`; `src/build_csv_distribution.py`; `docs/rdf_serialization.md` §§2–5.
- **Status:** done.
- **Presenter:**

## 4. Semantic data model

- **Message:** FHIR R4 structure plus standard terminologies, keeping MIMIC values next to standard codes.
- **Show:**
  - **Diagram:** Patient, Hospital Encounter, ICU Encounter, Location, Observation, Condition. The professor confirmed that a diagram is enough: the model reuses existing vocabularies, so no OWL file is needed.
  - **Terminologies:** LOINC, UCUM, HL7, SNOMED CT, ICD-9/10-CM.
  - **Key decisions**, pick 2–3:
    - time-resolved care-unit history (§9)
    - admission class separated from urgency (§8)
    - billed diagnosis, not presumed cause (§10)
    - qualified, broader-not-equivalent care-unit mappings (§9.2–9.3)
    - warning flag without implied abnormality (§5.6)
  - **Own terms:** two provisional extensions (warning, admission type). They appear only as `Extension.url` values under our W3ID base, never as new classes or properties.
  - **Before/after model:** the non-FHIR graph (SOSA/QUDT, from the CSVs) as the simpler comparison. It is not published.
- **Sources:** model §4 (DAG), §4.1 (backbone), §§5–10; provenance §§2–8; `rdf/mimic_icu_vitals_4h_csv_non_FHIR.ttl`.
- **Status:** model done; **diagram to make**.
- **Presenter:**

## 5. Metadata schema and publication

- **Message:** a DCAT record for the dataset and three distributions, validated by our SHACL shapes and reachable through W3IDs.
- **Show:**
  - **Shapes** (`metadata/mimic-iv-shacl_metadata.ttl`): Dataset, Distribution, Organization, and the properties they require; built in Contour.
  - **Dataset record** (`metadata/mimic-iv-RDF_metadata.ttl`):
    - creator MIT LCP, publisher Group 04;
    - licence ODbL 1.0 (share-alike, inherited from the source); access rights EU `PUBLIC`;
    - provenance: `dct:source` the Demo DOI, `prov:wasDerivedFrom` the Demo page;
    - `dct:references` FHIR R4 and the shapes;
    - MeSH theme and a keyword.
  - **Three distributions,** as the professor suggested ("ideally all 3"):
    - `source`: the upstream Demo ZIP on PhysioNet;
    - `csv`: our 5-table extract as a reproducible ZIP;
    - `rdf`: the FHIR-aligned Turtle.
  - **Resolution:** W3ID redirects live through the course relay. With `Accept: text/turtle`, `dataset/mimic-iv` returns the record; in a browser, the repository.
  - **Publication:** FAIR Data Point (catalogue, dataset, distributions).
- **Sources:** `metadata/`; `w3id/.htaccess` and `w3id/tests.yaml`.
- **Status:** shapes, record and redirects **done**; FDP **in progress**.
- **Presenter:**

## 6. FAIRness improvements

- **Message:** concrete gains, each tied to a FAIR principle and shown, not asserted, with the regressions stated.
- **Show:**
  - **Headline:** RDA FAIR Data Maturity Model self-assessment, 41 indicators. Original 24 met → FAIRified 34 met.
  - **Table** of principle → before → after:
    - **F1:** dataset DOI only, local keys for records → W3IDs for every resource and distribution, live.
    - **A1:** the DOI resolves to a web page → identifiers resolve to the data itself.
    - **I1/I2:** CSV with local itemids, labels and units → RDF with LOINC, UCUM, HL7, SNOMED and canonical ICD beside the source values.
    - **I3:** foreign keys → typed links (`subject`, `partOf`, `diagnosis` with billing role).
    - **R1.1/R1.2:** licence and provenance in machine-readable metadata; reproducible generation.
  - **Honest regressions:** F4 (indexing) and A2 (metadata outliving the data) are met by the original through DataCite, not by ours. The FDP should fix F4; A2 needs an archive deposit or stays a limitation.
  - **Before/after demo:** a similar question on both graphs. Non-FHIR `sparql/non-fhir/01_measure_summary.rq` groups by local label; FHIR `sparql/fhir/02_observations_per_loinc_code.rq` groups by LOINC code, which other datasets share.
- **Sources:** `docs/fair_assessment.md`; `sparql/`; README "FAIRification claims"; model §3.5.
- **Status:** done; update the counts after the FDP goes live.
- **Presenter:**

## Closing: limitations (Q&A backup)

- Not strict FHIR-RDF; no ShEx validation.
- Timestamps without timezone.
- Provisional extensions; their URLs redirect to the `docs/` folder, not to definitions.
- Browsers resolving a `data#…` IRI land on the `rdf/` folder; there is no landing page.
- Draft MIMIC-FHIR systems.
- ICD codes format-normalized only.
- F4 and A2 not met (see section 6).
- **Sources:** `docs/rdf_serialization.md` §6; `docs/fair_assessment.md`.

---

## Q&A preparation

Questions will test each member on their own work and on the course. Both members should be able to answer:

- What F1, A1, I2 and R1.2 mean, and where this project meets them.
- Why W3ID; what a 303 redirect does; why hash IRIs (`data#…`). The browser never sends the fragment, so every resource arrives at the relay as `data` and gets the whole file.
- Dataset vs distribution in DCAT; why three distributions of different scope.
- What SHACL validates and what it does not.
- What an FDP is for.
- Why FHIR, and why "aligned" and not "conformant".
- Why `dct:references` FHIR R4, not `dct:conformsTo`: no conformance was validated.
- Why LOINC and UCUM next to the MIMIC codes instead of replacing them.
- Why the non-FHIR graph is not published.

## Report sections that follow from this

| Section | Report section |
|---|---|
| 1–2 | Dataset, initial FAIR assessment, planning |
| 3 | Data preparation and transformation |
| 4 | Semantic model and decisions, with the diagram |
| 5 | Metadata schema and publication (add the FDP links when live) |
| 6 | Final FAIR assessment |
| Closing | Limitations and conclusions |
