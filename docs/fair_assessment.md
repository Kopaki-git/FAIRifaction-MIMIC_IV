# FAIR Self-Assessment

**Assessed:** 28 October 2026, after publication in a local FAIR Data Point (FDP).  
**Framework:** RDA FAIR Data Maturity Model, all 41 indicators with their priorities, as reproduced in [HL7 FHIR for FAIR — RDA Metrics](https://hl7.org/fhir/uv/fhir-for-fair/RDAMetrics.html) (specification: RDA, DOI 10.15497/RDA00050).

**Original:** MIMIC-IV Clinical Database Demo v2.2, as found on PhysioNet.
- Metadata: DOI `10.13026/dp1f-ex47` with its DataCite record; the landing page `https://physionet.org/content/mimic-iv-demo/2.2/` with embedded schema.org JSON-LD.
- Data: gzipped CSV tables under `https://physionet.org/files/mimic-iv-demo/2.2/`.

**FAIRified:**
- Metadata: `metadata/mimic-iv-RDF_metadata.ttl`, resolved via `https://w3id.org/FAIR-course-UT/2026/group04/dataset/mimic-iv`; also published as catalog, dataset and distribution records in a local FDP (exported to `fdp/export/`).
- Data: the three distributions (`…/dataset/mimic-iv/source`, `/csv`, `/rdf`) and the `data#…` resource IRIs.

This is a self-assessment by the project team, not an external evaluation. Several indicators are loosely worded, so each rating states its evidence.

## Summary

| Status | Original: all | Original: essential | FAIRified: all | FAIRified: essential |
|---|---:|---:|---:|---:|
| Met | 24 | 14 | 34 | 17 |
| Partly met | 10 | 6 | 5 | 2 |
| Not met | 6 | 0 | 1 | 1 |
| Not applicable | 1 | — | 1 | — |
| **Total** | **41** | **20** | **41** | **20** |

- **The original is already FAIR at the metadata level:** a DataCite DOI, schema.org metadata, open HTTPS access and a stated licence. Its gaps are in the **data**: CSV with local item codes, free-text care-unit labels and non-UCUM units, no machine-understandable representation, and no identifiers below dataset level.
- **The FAIRified version improves** data identifiers (F1-D), resolution to the data (A1-03D), data interoperability (I1-D, I2-D, I3-D) and metadata-to-data links (F3, I3-02M).
- **It does not match the original** on F4-01M (indexing) and A2-01M (metadata persistence), which the DOI's DataCite record provides. The FDP makes the metadata harvestable, but only locally, so F4-01M is partly met. A DOI-issuing archive deposit (e.g. Zenodo) would meet both.

## Template criteria (report tables)

The report template's assessment table lists F1–A2 criteria and stops at I1. The rows below keep the template's wording and add I1–R1.3. Each row aggregates the RDA indicators listed: **yes** if all are met, **no** if none are, otherwise **partially**. N/A indicators are ignored.

| Principle | Criterion | RDA indicators | Original | FAIRified |
|---|---|---|---|---|
| F1 | Globally unique identifier | F1-02M, F1-02D | partially | yes |
| F1 | Persistent identifier | F1-01M, F1-01D | partially | yes |
| F2 | Has metadata | — | yes | yes |
| F2 | Has rich metadata | F2-01M | partially | yes |
| F3 | Has data identifier in metadata | F3-01M | partially | yes |
| F3 | Has data identifier with clear predicate in metadata | F3-01M | partially (`schema:distribution` → landing page) | yes (`dcat:downloadURL`) |
| F4 | Indexed/registered in search resource | F4-01M | yes (DataCite) | partially (local FDP) |
| A1 | Has resolution protocol | A1-03M/D, A1-04M/D, A1-05D | partially | yes |
| A1.1 | Protocol is open, free and universally implementable | A1.1-01M/D | yes | yes |
| A1.2 | Protocol has authentication and authorisation mechanisms | A1.2-01D | N/A (open data) | N/A (open data) |
| A2 | Metadata has longer persistency than data | A2-01M | yes (DataCite) | **no** |
| I1 | (Meta)data use a formal, accessible, shared language | I1-01M/D, I1-02M/D | partially | yes |
| I2 | (Meta)data use FAIR vocabularies | I2-01M/D | partially | yes |
| I3 | (Meta)data include qualified references | I3-01M…I3-04M, I3-01D, I3-02D | partially | partially |
| R1 | Plurality of accurate, relevant attributes | R1-01M | yes | yes |
| R1.1 | Clear, accessible data usage licence | R1.1-01M…03M | yes | yes |
| R1.2 | Detailed provenance | R1.2-01M, R1.2-02M | partially | partially |
| R1.3 | Meets domain-relevant community standards | R1.3-01M/D, R1.3-02M/D | partially | partially |

The template asks for two initial tables, one for the dataset and one for its metadata. The M (metadata) and D (data) indicators below can be split that way.

## Indicators

Priority: E = essential, I = important, U = useful. "Orig" = the original, "Ours" = the FAIRified version.

### Findable

| ID | P | Indicator | Original | FAIRified | Evidence |
|---|---|---|---|---|---|
| F1-01M | E | Metadata identified by a persistent identifier | Met | Met | Orig: DOI. Ours: W3ID. |
| F1-01D | E | Data identified by a persistent identifier | Partly | Met | Orig: only the dataset as a whole (DOI); files have plain URLs and records have local keys. Ours: W3IDs for the distributions and every `data#…` resource. |
| F1-02M | E | Metadata identified by a globally unique identifier | Met | Met | DOI / W3ID |
| F1-02D | E | Data identified by a globally unique identifier | Partly | Met | As F1-01D |
| F2-01M | E | Rich metadata for discovery | Partly | Met | Orig: title, description, creators, version, date, licence; no keywords or subjects. Ours: adds MeSH theme D007362 and a keyword (only one: "ICU"). |
| F3-01M | E | Metadata includes the identifier of the data | Partly | Met | Orig: the DOI resolves to the landing page; JSON-LD `contentUrl` points to the page's file list. Ours: each distribution's `dcat:downloadURL` is its W3ID. |
| F4-01M | E | Metadata harvestable and indexable | Met | Partly | Orig: DataCite (state "findable") and JSON-LD for dataset search engines. Ours: published in an FDP, which exposes harvestable DCAT records, but the FDP runs locally and is not registered with any index. |

### Accessible

| ID | P | Indicator | Original | FAIRified | Evidence |
|---|---|---|---|---|---|
| A1-01M | I | Metadata contains access information | Met | Met | Orig: the landing page states open access and lists the files. Ours: access and download URLs; `dct:accessRights` = EU `PUBLIC`. |
| A1-02M | E | Metadata accessible manually | Met | Met | Landing page / dataset W3ID in a browser |
| A1-02D | E | Data accessible manually | Met | Met | File downloads |
| A1-03M | E | Metadata identifier resolves to a metadata record | Met | Met | Orig: DOI → landing page, or JSON-LD by content negotiation. Ours: dataset W3ID with `Accept: text/turtle` → the record. The FDP's record IRIs resolve too, but only on the local machine. |
| A1-03D | E | Data identifier resolves to a digital object | Partly | Met | Orig: the DOI resolves to a web page, not the data. Ours: `data#…` → the Turtle file; distribution W3IDs → their files. |
| A1-04M | E | Metadata accessed through a standardised protocol | Met | Met | HTTPS |
| A1-04D | E | Data accessible through a standardised protocol | Met | Met | HTTPS |
| A1-05D | I | Data accessible automatically | Met | Met | Open HTTPS downloads, no login needed |
| A1.1-01M | E | Metadata accessible through a free protocol | Met | Met | HTTPS |
| A1.1-01D | I | Data accessible through a free protocol | Met | Met | HTTPS |
| A1.2-01D | U | Protocol supports authentication and authorisation | N/A | N/A | Open data |
| A2-01M | E | Metadata guaranteed to remain available after the data | Met | **Not met** | Orig: the DataCite record persists independently of PhysioNet. Ours: metadata and data share one GitHub repository and there is no archive. Options: a DOI-issuing archive deposit, or stating it as a limitation. |

### Interoperable

| ID | P | Indicator | Original | FAIRified | Evidence |
|---|---|---|---|---|---|
| I1-01M | I | Metadata in a standardised knowledge representation format | Met | Met | Orig: JSON-LD, DataCite JSON. Ours: RDF Turtle. |
| I1-01D | I | Data in a standardised knowledge representation format | Not met | Met | Orig: CSV, a tabular format, not knowledge representation. Ours: RDF. |
| I1-02M | I | Metadata uses machine-understandable knowledge representation | Met | Met | schema.org JSON-LD / DCAT in RDF |
| I1-02D | I | Data uses machine-understandable knowledge representation | Not met | Met | Orig: meaning lives in column names and documentation. Ours: FHIR R4 classes and predicates. |
| I2-01M | I | Metadata uses FAIR-compliant vocabularies | Met | Met | Orig: schema.org, DataCite. Ours: DCAT, DCT, FOAF, PROV, MeSH, EU access-right, IANA. |
| I2-01D | U | Data uses FAIR-compliant vocabularies | Partly | Met | Orig: ICD-9/10 codes are standard; itemids, care-unit labels and units (e.g. "bpm") are local. Ours: adds LOINC, UCUM, HL7, SNOMED CT and canonical ICD. |
| I3-01M | I | Metadata references other metadata | Met | Met | Orig: DataCite `IsVersionOf` concept DOI. Ours: `dct:source`, `prov:wasDerivedFrom`. |
| I3-01D | U | Data references other data | Partly | Met | Orig: foreign keys (`subject_id`, `hadm_id`, `stay_id`) only. Ours: IRI links between resources. |
| I3-02M | U | Metadata references other data | Partly | Met | Orig: the JSON-LD distribution points to the landing page's file list. Ours: the `source` distribution resolves to the upstream files. |
| I3-02D | U | Data includes qualified references to other data | Not met | Met | Orig: relationships are implicit in column names. Ours: typed FHIR links (`subject`, `partOf`, `diagnosis` with billing role). |
| I3-03M | I | Metadata includes qualified references to other metadata | Met | Met | `IsVersionOf` / `prov:wasDerivedFrom` |
| I3-04M | U | Metadata includes qualified references to other data | Not met | Partly | Ours: `dcat:distribution` links the three distributions, but how the extract derives from the source is stated only in their titles. |

### Reusable

| ID | P | Indicator | Original | FAIRified | Evidence |
|---|---|---|---|---|---|
| R1-01M | E | Plurality of accurate and relevant attributes | Met | Met | Both records describe their own dataset accurately |
| R1.1-01M | E | Metadata includes licence information | Met | Met | Orig: licence in JSON-LD and on the page (not in the DataCite record). Ours: `dct:license`. |
| R1.1-02M | I | Metadata refers to a standard reuse licence | Met | Met | ODbL 1.0 |
| R1.1-03M | I | Metadata refers to a machine-understandable licence | Met | Met | Licence IRI |
| R1.2-01M | I | Provenance according to community-specific standards | Partly | Partly | Orig: origin and de-identification described in text; `IsVersionOf`. Ours: derivation from the Demo stated; the transformation is not modelled as provenance (deliberately). |
| R1.2-02M | U | Provenance in a cross-community language | Not met | Met | Ours: PROV-O (`prov:wasDerivedFrom`) |
| R1.3-01M | E | Metadata complies with a community standard | Met | Met | Orig: DataCite and schema.org. Ours: DCAT, validated against the project SHACL shapes and by the FDP against its schemas, extended with ours. |
| R1.3-01D | E | Data complies with a community standard | Partly | Partly | Orig: MIMIC's documented schema is a de facto standard in critical-care research, not a formal one. Ours: standard terminology codes; FHIR R4-aligned, not strict FHIR-RDF (`docs/rdf_serialization.md` §6). |
| R1.3-02M | E | Metadata expressed in a machine-understandable community standard | Met | Met | JSON-LD / DCAT in RDF |
| R1.3-02D | I | Data expressed in a machine-understandable community standard | Not met | Partly | Ours: RDF using FHIR's vocabulary, not conformant FHIR-RDF |

## Notes affecting interpretation

- **Scope differs.** The original rates the complete Demo release; the FAIRified data covers a five-table extract of it. The comparison is about how the data is represented, not how much of it there is.
- **Browsers vs programs.** A `data#…` IRI resolves to the whole Turtle file. Programs select the resource from the file. Browsers land on the repository's `rdf/` folder. The A1 ratings are for machine resolution.
- **Media type.** GitHub serves the Turtle files as `text/plain`, not `text/turtle`, so RDF tools may need to be told the format.
- **Accuracy is the team's assertion.** For example, R1-01M rates whether the record is accurate as far as the team knows; no indicator verifies it externally.

- **Local FDP.** The course requires only a local FDP. Its records and IRIs (`http://localhost:8085/…`) exist only on the machine running it; the W3IDs remain the public route to the metadata.

## Open

- Decide A2-01M: a DOI-issuing archive deposit, or a stated limitation.
