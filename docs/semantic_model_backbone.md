# Semantic Model — Backbone View

**Status:** Derived inspection view of the canonical semantic model.  
**Canonical source:** `docs/semantic_model_mapping.md`.  
**Authority:** This document is **not** an independent model. If this view and the canonical model ever diverge, the canonical model wins.

## Purpose

The canonical DAG is intentionally complete enough to expose the full FHIR structure and terminology mappings, but that makes it too large for quick orientation.

This backbone view is derived from the canonical model using one rule:

> Preserve every resource-level property needed to see what properties actually exist in the model, but compress datatype, terminology, and mapping internals unless their internal structure is itself necessary to understand the model topology.

This means absence is meaningful: a resource property is not silently dropped just to make the diagram smaller. Instead, complex internals are collapsed into bracketed summaries such as `[MIMIC item coding + LOINC]` or `[closest applicable HL7 care-setting role + SNOMED where defensibly specific]`.

Resource labels such as `Observation`, `Encounter`, `Condition`, and `Location` imply their FHIR resource type, so separate `rdf:type` branches are omitted from this simplified view.

## Backbone DAG

```text
Observation
│
├── status ──────────────────────────────▶ final
│
├── category ────────────────────────────▶ vital-signs
│
├── code ────────────────────────────────▶ [MIMIC item coding + LOINC]
│
├── subject ─────────────────────────────▶ Patient
│                                          │
│                                          └── identifier
│                                              ─────────▶ subject_id
│
├── effectiveDateTime ───────────────────▶ charttime
│
├── valueQuantity ───────────────────────▶ Quantity
│                                          │
│                                          ├── value ──▶ valuenum
│                                          └── unit ───▶ [source valueuom + UCUM]
│
├── extension ───────────────────────────▶ [warning flag]
│
└── encounter ───────────────────────────▶ ICU Encounter
                                           │
                                           ├── identifier
                                           │   ─────────▶ stay_id
                                           │
                                           ├── status
                                           │   ─────────▶ finished
                                           │
                                           ├── class
                                           │   ─────────▶ ACUTE
                                           │
                                           ├── subject
                                           │   ─────────▶ Patient
                                           │
                                           ├── period
                                           │   ─────────▶ ICU interval
                                           │              [intime → outtime]
                                           │
                                           ├── partOf
                                           │   ─────────▶ Hospital Encounter
                                           │              │
                                           │              ├── identifier
                                           │              │   ─────────▶ hadm_id
                                           │              │
                                           │              ├── status
                                           │              │   ─────────▶ finished
                                           │              │
                                           │              ├── class
                                           │              │   ─────────▶ IMP
                                           │              │
                                           │              ├── priority
                                           │              │   ─────────▶ [EL / UR / EM
                                           │              │               where mapped]
                                           │              │
                                           │              ├── extension
                                           │              │   ─────────▶ [verbatim
                                           │              │               admission_type]
                                           │              │
                                           │              ├── subject
                                           │              │   ─────────▶ Patient
                                           │              │
                                           │              ├── period
                                           │              │   ─────────▶ hospital interval
                                           │              │              [admittime → dischtime]
                                           │              │
                                           │              └── diagnosis
                                           │                  ─────────▶ EncounterDiagnosis
                                           │                              │
                                           │                              ├── rank
                                           │                              │   ─────▶ 1
                                           │                              │
                                           │                              ├── use
                                           │                              │   ─────▶ billing
                                           │                              │
                                           │                              └── condition
                                           │                                  ─────▶ Condition
                                           │                                          │
                                           │                                          ├── subject
                                           │                                          │   ─────▶ Patient
                                           │                                          │
                                           │                                          ├── encounter
                                           │                                          │   ─────▶ Hospital Encounter
                                           │                                          │
                                           │                                          ├── category
                                           │                                          │   ─────▶ encounter-diagnosis
                                           │                                          │
                                           │                                          └── code
                                           │                                              ─────▶ [source ICD +
                                           │                                                       canonical ICD]
                                           │
                                           └── location
                                               ─────────▶ EncounterLocation
                                                           │
                                                           ├── period
                                                           │   ───────▶ transfer interval
                                                           │             [intime → outtime]
                                                           │
                                                           └── location
                                                               ───────▶ Location
                                                                         │
                                                                         ├── mode
                                                                         │   ─────▶ kind
                                                                         │
                                                                         ├── name
                                                                         │   ─────▶ source careunit
                                                                         │
                                                                         └── type
                                                                             ─────▶ [closest applicable
                                                                                      HL7 care-setting role
                                                                                      + SNOMED where
                                                                                      defensibly specific]
```

## Reading this view

The backbone deliberately keeps resource properties such as `status`, `class`, `priority`, `category`, `identifier`, and extensions visible. What it hides is the lower-level representation machinery: individual `CodeableConcept`/`Coding` nodes, terminology-system URIs, complete mapping tables, extension canonical URLs, and similar details.

For the full mapping logic, exact coding systems, care-unit mapping table, admission-priority mapping, ICD handling, and deferred implementation decisions, use the canonical specification in `docs/semantic_model_mapping.md`.
