# FAIR MIMIC-IV — Semantic Mapping Provenance

**Status:** Proposed documentation of approved modelling decisions  
**Companion document:** `docs/semantic_model_mapping.md`  
**Dataset:** MIMIC-IV Clinical Database Demo v2.2 — first four hours of ICU stays, restricted to heart rate, respiratory rate and SpO₂.

## Purpose and scope

This document records the final, evidence-based justifications for the semantic modelling choices in the FAIRification project. It explains why selected ontology terms fit the source data, which relevant alternatives were considered, and what limitations remain.

It is a record of **modelling-decision provenance**, not a chronological account of every candidate explored. It also differs from **dataset derivation provenance**, which describes how the source extract was produced.

A mapping documented here is an approved modelling choice, not necessarily a factual equivalence established independently of the project. Where terminology verification or source interpretation remains uncertain, that limitation is stated explicitly.

---

## 1. Measurement representation

| Approved mapping | Justification and alternatives |
|---|---|
| **`IAO:0000109` — measurement datum** | MIMIC records charted measurement results, which IAO represents as information entities rather than physiological states or measurement processes. **Alternatives:** IAO's *scalar measurement datum* imposes a more specific unit-label structure; FHIR Observation and SPHN Measurement introduce clinical exchange or measurement-process structures. None adds a demonstrated benefit for our datum-centred model. |
| **`skos:Concept` + `dcterms:type`** | MIMIC `itemid` identifies a reusable measurement category, and SKOS preserves that category independently of individual observations. **Alternatives:** a plain literal loses the explicit reusable concept identity; modelling each category as an OWL class changes its ontological role. `dcterms:subject` would express what the observation is *about*, whereas `dcterms:type` expresses its classification. |
| **`sio:has value` + `sio:has unit`** | SIO directly represents the numerical value and associated unit of a measurement datum. **Alternative:** a separate Quantity/Result entity, as in SPHN's measurement representation, adds intermediate resources without supplying information required by our dataset or competency questions. |
| **QUDT units** | QUDT provides identifiable RDF resources for beats/minute, breaths/minute and percent, allowing standardized unit links. **Alternative:** UCUM supplies standardized unit codes and is also suitable for interoperability. QUDT was selected because its unit resources fit our RDF graph directly, not because UCUM was shown to be semantically inferior. |
| **`dcterms:date`** | The source provides a charted observation timestamp, without guaranteeing the exact measurement or recording event time. **Alternative:** `prov:generatedAtTime` would specifically describe when an entity was generated, which is not established by `charttime`. The broader DCMI property avoids that unsupported assertion. |
| **Local `warningFlag`** | The source warning value must be preserved without assuming clinical abnormality or measurement invalidity. **Alternative:** a standardized clinical interpretation or data-quality property would be preferable only if its definition matched the documented meaning of the MIMIC flag. That correspondence has not been established, so a narrowly defined local property is more defensible. |

**Evidence qualification:** The QUDT–UCUM comparison and the warning-flag alternative were not established as thoroughly as the IAO and SKOS comparisons. They should not be presented as equally well-validated comparative decisions.

**Supporting references**

- [MIMIC-IV — ICU chartevents](https://mimic.mit.edu/docs/iv/modules/icu/chartevents.html)
- [Information Artifact Ontology](https://github.com/information-artifact-ontology/IAO)
- [Semanticscience Integrated Ontology](https://github.com/MaastrichtU-IDS/semanticscience)
- [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/)
- [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
- [QUDT](https://qudt.org/)
- [UCUM](https://ucum.org/ucum)
- [HL7 FHIR Observation](https://hl7.org/fhir/R5/observation.html)
- [SPHN](https://sphn.ch/)

---

## 2. Care episodes and classifications

| Approved mapping | Justification and alternatives |
|---|---|
| **`sio:SIO_000006` — process (ICUStay and HospitalAdmission)** | An ICU stay and a hospitalization are time-bounded episodes of care, not merely database records or instantaneous admission events. SIO's process class captures that shared ontological nature. **Alternatives:** FHIR Encounter and OMOP visit structures offer more clinically specialized representations, but introduce additional exchange or data-model conventions without a demonstrated benefit for our bounded RDF model. |
| **`sio:SIO_000068` — is part of** | An ICU stay occurs within its corresponding hospitalization and can be modelled as a constituent episode of that larger care process. **Alternative:** `dcterms:isPartOf` offers a more general containment relationship, but SIO expresses the stronger process-level part–whole relationship that we intend. This is not merely a relationship between database records. |
| **`sio:SIO_000132` — has participant** | The patient participates in the hospitalization represented by `HospitalAdmission`. SIO expresses participation in a process without conflating the patient with the process or treating the patient as part of it. **Alternative:** a generic patient-association predicate could connect the resources, but would not express their ontological roles as precisely. |
| **`skos:Concept` — CareUnitTypeConcept and AdmissionTypeConcept** | Both source fields supply reusable institutional classifications: types of care units and types of admissions. SKOS preserves these as identifiable concepts that can be labelled and linked to external terminologies. **Alternatives:** plain string literals lose explicit concept identity and mappings; OWL classes would introduce class-level commitments unnecessary for representing the original categories. |
| **Direct ICUStay → CareUnitTypeConcept relationship** | MIMIC's `first_careunit` identifies the type of the first care unit associated with a stay, not an individually identified physical ward. A direct relationship retains this information without inventing an entity. **Alternatives:** SPHN's `Location` structure and physical-location predicates require a location instance rather than a SKOS category. The direct relationship is approved, but its exact predicate remains unresolved; a local property may be necessary. |

The `Patient` class itself and the predicates connecting observations to ICU stays and admissions to admission types remain unmapped. This section does not imply that vocabulary selections have been made for them.

**Supporting references**

- [MIMIC-IV — ICU stays](https://mimic.mit.edu/docs/iv/modules/icu/icustays.html)
- [MIMIC-IV — Hospital admissions](https://mimic.mit.edu/docs/iv/modules/hosp/admissions.html)
- [Semanticscience Integrated Ontology](https://github.com/MaastrichtU-IDS/semanticscience)
- [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/)
- [SPHN Semantic Framework](https://sphn.ch/)
- [HL7 FHIR](https://hl7.org/fhir/)
- [OMOP Common Data Model](https://ohdsi.github.io/CommonDataModel/)

---

## 3. SNOMED CT care-unit mappings

All nine source categories remain distinct MIMIC-local `skos:Concept` resources. SNOMED CT provides standardized care-setting concepts, while SKOS mapping properties communicate the strength of their correspondence.

| Approved mapping | Justification and alternatives |
|---|---|
| **MICU → Medical intensive care unit** (`441994008`, `exactMatch`) | Both concepts classify a medical ICU environment, rather than a treatment service or particular physical ward. **Alternative:** `closeMatch` would avoid asserting broad interchangeability, but the documented meanings align closely enough to support `exactMatch`. |
| **SICU → Surgical intensive care unit** (`418433008`, `exactMatch`) | Both concepts identify surgical intensive care as a care-unit category. **Alternative:** `closeMatch` is more conservative but offers no identified semantic advantage given the matching clinical specialization and entity type. |
| **MICU/SICU → Intensive care unit** (`309904001`, `broadMatch`) | The source describes combined medical/surgical intensive care. The general ICU concept preserves its care level without selecting only one specialization. **Alternatives:** mapping to either Medical ICU or Surgical ICU individually would lose part of the source meaning; asserting equivalence to generic ICU would discard the specialization distinction. |
| **TSICU → Surgical intensive care unit** (`418433008`, `broadMatch`) | The target preserves surgical intensive care while omitting the trauma specialization. **Alternative:** a generic trauma-care concept might preserve trauma but not necessarily surgical intensive care. The selected broader concept retains the underlying ICU setting. |
| **Neuro Surgical ICU → Neurological intensive care unit** (`309909006`, `broadMatch`) | The neurological ICU concept preserves the neurological specialization but not the surgical distinction. **Alternative:** Surgical ICU would preserve surgery but lose neurological specialization. The selected target is a defensible broader classification, not an assertion of equivalence. |
| **Neuro Stepdown → Stepdown unit** (`419590001`, `broadMatch`) | The target preserves the stepdown level of care without specifying neurological specialization. **Alternative:** High dependency unit is another intermediate-care category, but would not preserve the explicit stepdown designation as directly. |
| **CVICU → Intensive care unit** (`309904001`, `broadMatch`) | The source combines cardiac and vascular intensive care, whereas the general ICU concept encompasses the shared care setting. **Alternative:** Cardiac intensive care unit is more specific but does not establish coverage of the vascular component. Mapping to the general ICU avoids that unsupported restriction. |
| **CCU → Cardiac intensive care unit** (`309907008`, `broadMatch`) | Coronary care is a more specific cardiac critical-care setting. **Alternatives:** generic ICU would discard more clinical specificity; an exact mapping to Cardiac ICU would incorrectly treat broader cardiac care as interchangeable with coronary care. |
| **Neuro Intermediate → High dependency unit** (`397771005`, `broadMatch`) | BIDMC's neuro-intermediate setting provides monitoring and care between conventional ward care and the highest-acuity neuro-ICU. High dependency unit is a plausible broader care-level category. **Alternative:** Stepdown unit is related, but its correspondence to this particular institutional category is less clearly established. The selected mapping retains a plausible care-level interpretation while losing neurological specialization. |

### Shared limitations

The mappings express **terminological relationships**, not identity between physical hospital units. Broader targets deliberately lose specificity while preserving the original MIMIC category.

The strongest remaining uncertainty concerns Neuro Intermediate: the available clinical descriptions support its relationship to high-dependency care, but do not establish formal subsumption.

Release-specific SNOMED concept status and hierarchy verification also remain outstanding for all nine mappings. These are limitations of the current evidence, not claims that the mappings have already passed formal validation.

**Supporting references**

- [MIMIC-IV — ICU stays](https://mimic.mit.edu/docs/iv/modules/icu/icustays.html)
- [SNOMED CT Browser](https://browser.ihtsdotools.org/)
- [W3C SKOS Reference — Mapping properties](https://www.w3.org/TR/skos-reference/#mapping)
- BIDMC neurocritical-care documentation considered during the original care-unit mapping review.

---

## 4. Cross-cutting modelling decisions

| Decision | Justification and alternatives |
|---|---|
| **Selective ontology reuse** | The model combines IAO, SIO, SKOS, DCMI, QUDT and SNOMED CT because each serves a distinct semantic purpose. **Alternative:** adopting FHIR or SPHN as a complete framework could improve compatibility with their ecosystems, but would impose structures or constraints that our dataset does not require. Reuse is justified term by term, not by institutional prominence. |
| **Preservation of MIMIC-local identity** | Source identifiers and classifications remain available alongside standardized vocabulary links, allowing the transformed data to be traced back to MIMIC. **Alternative:** replacing local concepts with external identifiers would simplify some queries but could erase source-specific distinctions, particularly where only a broader SNOMED match exists. |
| **No redundant observation-to-patient or admission links** | The approved conceptual model connects observations through their ICU stays and hospital admissions, preserving the hierarchy represented by the source identifiers. **Alternative:** direct links could shorten queries but duplicate relationships already recoverable through the graph. They can be reconsidered if an implementation requirement justifies them. |
| **Standard predicates before local properties** | Established predicates are preferable when their definitions faithfully express the intended relationship. A local property is appropriate when available alternatives impose incorrect meanings—for example, treating a care-unit category as a physical location. **Alternative:** forcing an approximate standard predicate would provide vocabulary reuse at the expense of semantic correctness. |
| **Separation of data semantics and extraction provenance** | The observation model represents charted clinical data, while the first-four-hour selection rule describes how the derived dataset was constructed. **Alternative:** embedding the extraction window as a clinical property of each observation could imply that four hours has physiological significance. The rule belongs in derivation provenance instead. |

**Supporting references**

- [MIMIC-IV Documentation](https://mimic.mit.edu/docs/iv/)
- [MIMIC-IV Demo v2.2](https://physionet.org/content/mimic-iv-demo/2.2/)
- Repository `AGENTS.md` and canonical extraction notebook
- [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/)
- [IAO](https://github.com/information-artifact-ontology/IAO), [SIO](https://github.com/MaastrichtU-IDS/semanticscience), [DCMI](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/), and [QUDT](https://qudt.org/)

---

## 5. Outstanding modelling and verification work

The justifications above apply only to approved decisions. They do not settle the following:

- The `Patient` class, observation-to-stay predicate, and admission-type predicate have not been finalized.
- Source identifier properties, local property definitions and RDF URI schemes remain undecided.
- The external measurement terminology mappings for HR, RR and SpO₂ remain to be selected.
- The SNOMED mappings are approved modelling choices, but release-specific terminology validation is outstanding.

Future mappings should be accompanied by comparable justifications, including the strongest relevant alternative and any material evidence limitations.

The semantic mapping specification remains the authoritative record of the current graph. This provenance document explains its decisions without changing them.