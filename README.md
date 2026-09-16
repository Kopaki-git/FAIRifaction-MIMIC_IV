# FAIRification of a MIMIC-IV ICU Vital-Sign Extract

This repository contains a course project for **FAIR Data Engineering** at the University of Twente. The project takes a small, reproducible subset of the **MIMIC-IV Clinical Database Demo v2.2** and incrementally makes that resource more FAIR, with particular emphasis on **semantic interoperability**.

The project does **not** treat MIMIC-IV as an example of generally poor data stewardship. MIMIC-IV already has strong documentation, provenance, licensing, versioning, and accessibility. The main opportunity explored here is narrower: a user or software agent should not need MIMIC-specific knowledge to interpret local measurement identifiers, units, and relationships. The project therefore preserves MIMIC source semantics while adding explicit, machine-actionable semantic representations and mappings.

## Current project resource

The canonical tabular resource is:

```text
data/derived/mimic_icu_vitals_4h.csv
```

It contains three routinely charted ICU vital signs:

| MIMIC `itemid` | Source label | Source abbreviation | Source unit |
|---:|---|---|---|
| `220045` | Heart Rate | HR | bpm |
| `220210` | Respiratory Rate | RR | insp/min |
| `220277` | O2 saturation pulseoxymetry | SpO2 | % |

The extraction includes observations whose `charttime` lies in the first four hours of each represented ICU stay:

```text
[ICU intime, ICU intime + 4 hours)
```

The resulting dataset contains:

- **2,501 observations**
- **94 patients**
- **121 hospital admissions**
- **133 ICU stays**
- 859 heart-rate observations
- 860 respiratory-rate observations
- 782 pulse-oximetry oxygen-saturation observations

Every represented ICU stay contains all three selected measurement types.

### Why four hours?

The four-hour boundary is an **engineering scope choice**, not a clinical claim.

The course project is intended to operate on a bounded resource of at most a few thousand records. Instead of selecting an arbitrary random sample of rows, the project uses a temporal rule with a clear interpretation: *all selected vital-sign observations from the first four hours of each ICU stay*.

Candidate windows were compared during exploration:

| Window | Observations | Patients | ICU stays |
|---:|---:|---:|---:|
| 1 h | 856 | 79 | 109 |
| 2 h | 1,452 | 83 | 119 |
| 4 h | 2,501 | 94 | 133 |
| 6 h | 3,499 | 99 | 139 |
| 8 h | 4,497 | 100 | 140 |
| 24 h | 11,336 | 100 | 140 |

Four hours gives a conveniently sized resource while retaining broad coverage across the demo. No claim is made that four hours is clinically privileged.

## Source data

The project is derived from **MIMIC-IV Clinical Database Demo v2.2**, an openly available demonstration subset of MIMIC-IV containing data for 100 patients.

Source page:

- https://physionet.org/content/mimic-iv-demo/2.2/

The original downloaded MIMIC files are intentionally **not version-controlled in this repository**. They should be placed locally under:

```text
data/
├── hosp/
└── icu/
```

Only three source tables are required to recreate the canonical extract:

```text
data/icu/chartevents.csv.gz
data/icu/icustays.csv.gz
data/icu/d_items.csv.gz
```

Their roles are:

- `chartevents`: individual ICU observations and their charted values;
- `icustays`: ICU stay identifiers and ICU admission times (`intime`);
- `d_items`: MIMIC's dictionary for local `itemid` codes.

The repository's `.gitignore` keeps downloaded source data local while allowing derived project resources under `data/derived/` to be tracked.

## Reproducing the extract

The derivation is documented and executed in:

```text
notebooks/01_dataset_exploration_and_extraction.ipynb
```

The notebook is intentionally both exploratory and reproducible. It shows how the project resource was chosen rather than hiding the decision inside a production script.

Run the notebook from within the repository after placing the MIMIC-IV Demo files under `data/icu/` and `data/hosp/`.

The notebook:

1. loads the relevant columns from `chartevents`, `icustays`, and `d_items`;
2. inspects the source definitions of the three target measurements;
3. joins ICU admission time to charted observations;
4. compares candidate extraction windows;
5. applies the four-hour extraction rule;
6. joins the human-readable MIMIC measurement label;
7. validates coverage, missingness, duplicates, warning flags, and observed ranges;
8. runs reproducibility assertions;
9. writes `data/derived/mimic_icu_vitals_4h.csv`.

A successful run should reproduce the counts listed above.

### Time fields and deidentification

The extraction uses **`charttime`**, not `storetime`, to determine whether an observation falls in the first four hours of an ICU stay.

- `charttime` represents the charted time associated with the clinical observation.
- `intime` is the ICU admission time from `icustays`.
- `storetime` is not used to define the extraction window because it reflects entry/storage timing rather than the time represented by the observation.

MIMIC dates are shifted for deidentification. A timestamp such as `2180-07-23 14:12:00` is therefore **not a real calendar date**. Relative temporal structure is preserved, so elapsed time between ICU admission and observations remains usable.

## Canonical CSV schema

The derived CSV contains nine fields:

| Field | Meaning |
|---|---|
| `subject_id` | MIMIC-local patient identifier |
| `hadm_id` | MIMIC-local hospital-admission identifier |
| `stay_id` | MIMIC-local ICU-stay identifier |
| `charttime` | Deidentified charted observation timestamp |
| `itemid` | MIMIC-local identifier for the measurement type |
| `measurement_label` | Human-readable source label joined from `d_items` |
| `valuenum` | Numeric observation value |
| `valueuom` | Unit string as represented by MIMIC |
| `warning` | Source warning flag associated with the observation |

The source `itemid` and source unit strings are deliberately retained. Semantic FAIRification should **add mappings**, not erase source terminology.

## Validation status

The current canonical extract has passed the reproducibility checks in the notebook:

- 2,501 total observations;
- 94 unique patients;
- 121 unique hospital admissions;
- 133 unique ICU stays;
- expected per-measurement counts;
- no missing `valuenum` values;
- no missing `valueuom` values;
- no exact duplicates under patient, ICU stay, chart time, measurement type, and value;
- all 133 represented stays contain all three target measurement types.

Warning flags are retained rather than filtered:

- `warning = 0`: 2,500 observations
- `warning = 1`: 1 observation

Observed values are also preserved as supplied by MIMIC. Unusual values, such as respiratory rate `0` or SpO2 `64`, are **not automatically treated as errors** without source evidence supporting that conclusion.

## FAIRification problem framing

The current CSV is already structured and interpretable to a human who knows the MIMIC schema. For example, `itemid = 220045` can be joined to `d_items`, where it has the label `Heart Rate`.

However, that meaning remains **MIMIC-local**. A generic external system does not intrinsically know that:

- `220045` represents heart rate;
- `bpm` is the relevant unit representation;
- `stay_id` denotes an ICU encounter;
- an individual row represents a clinical observation;
- two differently coded observations in different datasets refer to the same physiological property.

The goal of semantic interoperability is not to make software "understand" physiology in a human sense. It is to represent enough distinctions and relationships formally that software can **identify, compare, query, validate, and combine** data without bespoke MIMIC-specific interpretation.

In later stages, the project will therefore make relationships explicit, for example conceptually:

```text
Patient
  -> Hospital admission
      -> ICU stay
          -> Clinical observation
              -> observed property
              -> numeric value
              -> unit
              -> observation time
```

MIMIC-local measurement concepts and units can then be linked to shared identifiers from established vocabularies where defensible.

A critical design principle is:

> Preserve the original MIMIC identifier and source meaning, then add qualified mappings to shared concepts.

The exact external vocabulary mappings are **not frozen yet** and should be selected during semantic modelling rather than guessed early.

## FAIR profile at project start

At a high level, the source resource begins from a relatively strong FAIR baseline:

### Findable

MIMIC-IV has stable dataset-level identification, versioning, citation guidance, and discoverability through PhysioNet. The derived observations and local concepts do not yet have globally resolvable semantic identifiers of their own.

### Accessible

The MIMIC-IV Demo is openly retrievable over standard web protocols. Accessibility is therefore not the main deficit being targeted in this project.

### Interoperable

The source data is well structured relationally, but important semantics are expressed through local MIMIC identifiers, unit strings, schema conventions, and documentation. This is the main focus of the project.

### Reusable

MIMIC-IV has strong documentation, provenance, and licensing. The derived resource still needs explicit machine-actionable provenance, semantic relations, metadata, identifiers, and publication artefacts for the course workflow.

FAIRness is treated as incremental rather than binary: the goal is to make this bounded resource **FAIRer**, not to claim that the original MIMIC data is non-FAIR.

## Planned semantic scope

The provisional semantic types needed to describe the resource are:

- Patient / subject
- Hospital admission
- ICU stay / encounter
- Clinical observation
- Observable or measurement type
- Numeric value / quantity
- Unit
- Observation time
- Warning / source-quality indicator

These are planning concepts, not yet commitments to particular ontology classes.

Provisional competency questions include:

- Which vital-sign observations belong to a particular ICU stay?
- Which patient and hospital admission does an ICU observation belong to?
- What physiological property does an observation measure?
- What numeric value and unit does an observation have?
- When was an observation charted?
- Can all heart-rate observations be retrieved without knowing the MIMIC `itemid`?
- Which observations carry a warning flag?

These questions should guide the semantic model and later SPARQL validation.

## Relationship to existing FHIR work

MIMIC-IV has already been transformed to FHIR in existing work. That is relevant prior work rather than a reason not to perform this project.

FHIR provides a common healthcare representation built around resources such as Patient, Encounter, and Observation. Existing MIMIC-to-FHIR work already makes much of the encounter/observation structure explicit.

However, ICU `chartevents` can still retain MIMIC-specific terminology for measurement codes and source units. Therefore, this project should **not claim novelty for representing observations or encounters**. Its useful focus is the semantic interoperability boundary between MIMIC-local ICU terminology and shared machine-actionable clinical vocabularies, together with the FAIR metadata, provenance, identifiers, Linked Data transformation, and publication workflow required by the course.

## Repository structure

Current high-level structure:

```text
FAIRifaction-MIMIC_IV/
├── AGENTS.md                                  # instructions/context for coding agents
├── README.md                                  # project overview and current state
├── .gitignore                                 # keeps source MIMIC data local
├── data/
│   ├── derived/
│   │   └── mimic_icu_vitals_4h.csv            # canonical project resource
│   ├── hosp/                                  # local MIMIC source data; ignored
│   └── icu/                                   # local MIMIC source data; ignored
├── notebooks/
│   └── 01_dataset_exploration_and_extraction.ipynb
└── src/
    └── explore_data.py                        # earlier exploratory code
```

The notebook supersedes `src/explore_data.py` as the authoritative record of the canonical extraction decision. The older script may remain as exploratory history unless deliberately removed later.

## Project stages

The current project progression is:

1. **Freeze the source resource** — complete. Reproducible extraction notebook and canonical CSV exist.
2. **Document the source resource** — current stage. Define field meaning, derivation, provenance, and assumptions clearly.
3. **FAIRification planning and initial assessment** — stakeholders, requirements, semantic types, competency questions, target FAIR improvements.
4. **Semantic data modelling** — define the observation model and select/reuse suitable vocabularies.
5. **Linked Data transformation** — generate RDF with stable identifiers and explicit semantic mappings.
6. **Semantic metadata modelling** — describe the dataset/distributions/provenance and define validation constraints such as SHACL where appropriate.
7. **Publication** — publish data and metadata using the course workflow, including repository publication, persistent identifier/redirection infrastructure, and FAIR Data Point metadata where required.
8. **Reassessment** — compare the resource before and after FAIRification and document remaining limitations.

The implementation should remain deliberately small enough that the semantic model can be inspected and justified rather than becoming a large data-engineering exercise.

## External linking direction

A natural later linking target is the **MIMIC-IV-ED Demo**, which uses the same demonstration patient population and contains emergency-department vital signs.

One possible cross-dataset question is:

> For patients progressing from the emergency department to the ICU, can semantically aligned heart-rate, respiratory-rate, and oxygen-saturation observations be queried across both representations without relying on source-specific codes?

Actual cross-dataset SPARQL integration is optional/bonus scope and should not distract from completing the core FAIRification workflow first.

## Installation

The current notebook requires Python and pandas. A minimal environment is:

```bash
python3 -m pip install pandas jupyter
```

Then launch Jupyter from the repository or a parent directory and run:

```text
notebooks/01_dataset_exploration_and_extraction.ipynb
```

Use **Restart Kernel and Run All** as the reproducibility check.

## Licensing and attribution

The source MIMIC-IV Demo release is distributed by PhysioNet under its stated license terms. Consult the source release directly before redistributing derived data or changing publication scope:

- https://physionet.org/content/mimic-iv-demo/2.2/

The source license and attribution requirements remain applicable to derivative work. This repository should preserve clear provenance to the exact MIMIC-IV Demo version used.

## Development principles

When extending this repository:

- keep source MIMIC identifiers rather than replacing them;
- distinguish source facts from semantic mappings added by this project;
- do not introduce clinical claims merely to justify engineering choices;
- do not silently clean or exclude unusual observations without evidence;
- keep the canonical CSV derivation reproducible from the source demo;
- prefer explicit, inspectable semantic modelling over unnecessary pipeline complexity;
- treat mappings to external vocabularies as claims that require justification;
- update documentation when project decisions become fixed.

See [`AGENTS.md`](AGENTS.md) for detailed instructions intended for Codex and other coding agents working on the repository.
