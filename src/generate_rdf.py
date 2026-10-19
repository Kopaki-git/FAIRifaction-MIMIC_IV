"""Generate FHIR R4-aligned RDF (Turtle) from the canonical MIMIC-IV ICU vital-sign resource.

Implements the frozen model in docs/semantic_model_mapping.md using the identifier and
serialization decisions recorded in docs/rdf_serialization.md. The output is simplified
FHIR-predicate RDF: R4 predicate IRIs without fhir:value / fhir:link / fhir:index machinery.
It does not claim strict FHIR-RDF serialization or FHIR instance conformance.

Usage: python src/generate_rdf.py [--source DIR] [--output PATH]
"""

import argparse
import csv
import re
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "derived" / "mimic_icu_vitals_4h"
DEFAULT_OUTPUT = ROOT / "rdf" / "mimic_icu_vitals_4h.ttl"

# =============================================================================
# Configuration (from here down to ICD_CODE): every decision lives here as
# data, not inside the logic below.
#
# - Decisions (W3ID year, terminology mappings) change for different reasons
#   than mechanics (how triples are built). Keeping them here means a decision
#   can be reviewed or changed without touching any function.
# - Each URI is defined once as a constant. A typo inside a repeated string
#   silently produces wrong RDF; a typo in a constant name fails immediately
#   with NameError. DATA and the extension URLs are built from W3ID_BASE so
#   they cannot drift apart.
# - Mapping tables are dictionaries shaped like the tables in
#   docs/semantic_model_mapping.md (section cited above each), so they can be
#   checked against the model row by row. Their keys are the complete list of
#   approved source values; lookup() rejects anything else. None means
#   "considered and deliberately not mapped", unlike a missing key, which
#   means "never considered".
# - FHIR and DATA are rdflib Namespaces because they produce graph nodes
#   (predicates and resources). Terminology systems are plain strings because
#   FHIR fields such as Coding.system hold URI values, not links; they are
#   written as plain string literals, as in R4 FHIR-RDF (see uri()).
# - TIMESTAMP, DECIMAL and ICD_CODE are the formats source values must match;
#   the value helpers raise an error on anything else.
# - The tables were copied by hand from the model. tests/test_rdf.py keeps its
#   own separate copy, so a copying mistake would have to happen twice to go
#   unnoticed.
# =============================================================================

# --- Namespaces and project identifiers (docs/rdf_serialization.md, D1, D2, D6) ---

FHIR = Namespace("http://hl7.org/fhir/")
W3ID_BASE = "https://w3id.org/FAIR-course-UT/2026-2027/group4/"
DATA = Namespace(W3ID_BASE + "data#")

EXT_WARNING = W3ID_BASE + "fhir/StructureDefinition/observation-mimic-warning"
EXT_ADMISSION_TYPE = W3ID_BASE + "fhir/StructureDefinition/encounter-mimic-admission-type"

# --- MIMIC-local identifier systems and CodeSystems, reused from MIMIC-FHIR (D4, D5) ---

MIMIC_FHIR = "http://mimic.mit.edu/fhir/mimic/"
ID_PATIENT = MIMIC_FHIR + "identifier/patient"
ID_ENCOUNTER_HOSP = MIMIC_FHIR + "identifier/encounter-hosp"
ID_ENCOUNTER_ICU = MIMIC_FHIR + "identifier/encounter-icu"
CS_MIMIC_ITEMS = MIMIC_FHIR + "CodeSystem/mimic-chartevents-d-items"

# --- Standard terminology systems (model §§5-10) ---

LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
SNOMED = "http://snomed.info/sct"
HL7_CS = "http://terminology.hl7.org/CodeSystem/"
OBSERVATION_CATEGORY = HL7_CS + "observation-category"
ACT_CODE = HL7_CS + "v3-ActCode"
ACT_PRIORITY = HL7_CS + "v3-ActPriority"
ROLE_CODE = HL7_CS + "v3-RoleCode"
DIAGNOSIS_ROLE = HL7_CS + "diagnosis-role"
CONDITION_CATEGORY = HL7_CS + "condition-category"

# --- Approved mappings, transcribed from docs/semantic_model_mapping.md ---

# §6.1 and §6.2: itemid -> source label, LOINC code(s), source unit, UCUM code.
ITEMS = {
    "220045": {"label": "Heart Rate", "loinc": ["8867-4"], "unit": "bpm", "ucum": "/min"},
    "220210": {"label": "Respiratory Rate", "loinc": ["9279-1"], "unit": "insp/min", "ucum": "/min"},
    "220277": {"label": "O2 saturation pulseoxymetry", "loinc": ["2708-6", "59408-5"], "unit": "%", "ucum": "%"},
}

# §5.6: source warning -> valueBoolean.
WARNING = {"0": False, "1": True}

# §8.2: admission_type -> Encounter.priority code; None means no priority is asserted.
ADMISSION_PRIORITY = {
    "ELECTIVE": "EL",
    "URGENT": "UR",
    "EW EMER.": "EM",
    "DIRECT EMER.": "EM",
    "OBSERVATION ADMIT": None,
    "SURGICAL SAME DAY ADMISSION": None,
}

# §9.2 and §9.3: careunit -> Location.type CodeableConcepts, each a list of (system, code) codings.
CARE_UNIT_TYPES = {
    "Medical Intensive Care Unit (MICU)": [[(ROLE_CODE, "ICU"), (SNOMED, "441994008")]],
    "Surgical Intensive Care Unit (SICU)": [[(ROLE_CODE, "ICU"), (SNOMED, "418433008")]],
    "Medical/Surgical Intensive Care Unit (MICU/SICU)": [[(ROLE_CODE, "ICU")]],
    "Trauma SICU (TSICU)": [[(ROLE_CODE, "ICU")]],
    "Neuro Surgical Intensive Care Unit (Neuro SICU)": [[(ROLE_CODE, "ICU")], [(ROLE_CODE, "NS")]],
    "Neuro Stepdown": [[(ROLE_CODE, "HU")]],
    "Cardiac Vascular Intensive Care Unit (CVICU)": [[(ROLE_CODE, "ICU")]],
    "Coronary Care Unit (CCU)": [[(ROLE_CODE, "CCU")]],
    "Neuro Intermediate": [[(ROLE_CODE, "HU")]],
}

# §10.3: icd_version -> (MIMIC source CodeSystem, canonical ICD system).
ICD_SYSTEMS = {
    "9": (MIMIC_FHIR + "CodeSystem/mimic-diagnosis-icd9", "http://hl7.org/fhir/sid/icd-9-cm"),
    "10": (MIMIC_FHIR + "CodeSystem/mimic-diagnosis-icd10", "http://hl7.org/fhir/sid/icd-10-cm"),
}

TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
DECIMAL = re.compile(r"^-?\d+(\.\d+)?$")
ICD_CODE = re.compile(r"^[A-Z0-9]+$")


# =============================================================================
# IRI minting (D2): one function per resource kind turns source keys into
# that resource's IRI.
#
# - RDF has no joins: two nodes are the same resource only if their IRIs match
#   character for character. Rows from different tables that mention the same
#   patient, encounter or condition connect only because they call the same
#   function here, so these functions are where the tables get joined.
# - IRIs are built from source keys, never from counters or random IDs, so the
#   same input always yields the same IRI regardless of row order or run.
# - Every IRI carries a type prefix because MIMIC reuses numbers across ID
#   spaces, and condition and hospital-encounter IRIs share hadm_id by design.
#   Without the prefix those resources would merge into one node.
# - The MIMIC IDs embedded here are not where those IDs are recorded as data.
#   Each resource also carries an explicit FHIR Identifier (model §3.1); query
#   that, and never parse IDs out of IRIs.
# =============================================================================

def patient_iri(subject_id):
    return DATA[f"patient-{subject_id}"]


def hospital_encounter_iri(hadm_id):
    return DATA[f"hospital-encounter-{hadm_id}"]


def icu_encounter_iri(stay_id):
    return DATA[f"icu-encounter-{stay_id}"]


def condition_iri(hadm_id):
    return DATA[f"condition-{hadm_id}"]


def observation_iri(stay_id, charttime, itemid):
    """Return the Observation IRI built from (stay_id, charttime, itemid).

    Observation rows have no source ID, so the IRI uses this composite key,
    which is unique across all 2,501 source rows. A collision would be silent
    in RDF: two rows would merge into one Observation carrying two values, so
    add_observation() stops on a duplicate IRI.

    charttime is compacted ("2180-07-23 14:12:00" -> "21800723T141200")
    because IRIs cannot contain spaces; the compact ISO form stays readable
    and sorts chronologically.
    """
    stamp = charttime.replace("-", "").replace(":", "").replace(" ", "T")
    return DATA[f"observation-{stay_id}-{stamp}-{itemid}"]


def location_iri(careunit):
    """Return the Location IRI derived from the verbatim care-unit label.

    Care units have no source ID, only a label. The slug (lowercase, with each
    run of non-alphanumeric characters replaced by "-") is derived from the
    label by rule rather than from hand-picked short names, so there is no
    extra mapping table to review. Trade-offs: a renamed label in a later MIMIC
    release changes the IRI, and two labels differing only in punctuation would
    collapse into one IRI. The generator does not check for that; the test
    requiring exactly 9 Locations would catch it.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", careunit.lower()).strip("-")
    return DATA[f"location-{slug}"]


# =============================================================================
# Value helpers: how source values become RDF literals. Each helper checks the
# format its conversion relies on and raises ValueError rather than writing a
# value that quietly differs from the source.
# =============================================================================

def lookup(table, key, field):
    """Return table[key], or raise ValueError naming the field and value.

    Used for both mapping tables and integrity lookups. Unlike a bare
    table[key] (KeyError: 'X'), the message says which field failed and that
    the value is outside the approved mapping, pointing the reader back to the
    model rather than the code.
    """
    if key not in table:
        raise ValueError(f"{field} value {key!r} is outside the approved mapping")
    return table[key]


def uri(value):
    """Return a FHIR uri value (e.g. Coding.system) as a plain string literal.

    The value is text that happens to be a URI, not a link, so it is not an
    IRI node. It is untyped because R4 FHIR-RDF writes uri values as plain
    strings (R5 would type them xsd:anyURI), which also lets SPARQL match them
    with a plain string such as "http://loinc.org". Kept as a function so this
    choice lives in one place.
    """
    return Literal(value)


def date_time(value):
    """Return a source timestamp as an xsd:dateTime literal, text preserved.

    The conversion only replaces the space with "T", which is correct only for
    the exact shape YYYY-MM-DD HH:MM:SS, so that shape is checked first. The
    value is not parsed into a datetime and reformatted, so no characters can
    change, and no timezone is added because MIMIC provides none (D7).
    """
    if not TIMESTAMP.match(value):
        raise ValueError(f"unexpected timestamp format: {value!r}")
    return Literal(value.replace(" ", "T"), datatype=XSD.dateTime, normalize=False)


def decimal(value):
    """Return a source number as an xsd:decimal literal, text preserved.

    FHIR treats decimal precision as meaningful ("91.0" is not "91"), so the
    exact source text is kept: xsd:decimal rather than a float, and
    normalize=False so RDFLib does not rewrite it (e.g. "080.50" -> "80.50").
    Empty, "nan" and scientific-notation values are rejected.
    """
    if not DECIMAL.match(value):
        raise ValueError(f"unexpected numeric value: {value!r}")
    return Literal(value, datatype=XSD.decimal, normalize=False)


def canonical_icd(code, version):
    """Insert the standard ICD-9-CM / ICD-10-CM decimal point without otherwise changing the code.

    The dot goes after three characters, except ICD-9-CM E-codes (external
    causes), which take four: E8790 -> E879.0. In ICD-10-CM "E" means
    endocrine and follows the three-character rule (E1165 -> E11.65), so the
    version decides the rule, not the letter alone.

    Guards: the code must be undotted letters and digits, and the version must
    be approved. lookup() is called only for its error, so the function is safe
    even when a caller (such as a test) has not checked the version first.
    It formats codes only and does not check that a code exists in an ICD release.
    """
    if not ICD_CODE.match(code):
        raise ValueError(f"unexpected ICD code: {code!r}")
    lookup(ICD_SYSTEMS, version, "icd_version")
    # ICD-9-CM E-codes carry four characters before the decimal; all other codes carry three.
    split = 4 if version == "9" and code.startswith("E") else 3
    return code if len(code) <= split else f"{code[:split]}.{code[split:]}"


# =============================================================================
# Datatype builders: FHIR's reusable structures (Coding, CodeableConcept,
# Identifier, Period, Extension). Each builder creates a blank node (D3),
# attaches its fields and returns the node; the caller chooses the predicate
# that attaches it, because the same structure appears under different parents.
# =============================================================================

def coding(g, system, code, display=None):
    """Return a Coding blank node with system, code and optional display.

    Display is written only when given. The model specifies it only for the
    MIMIC item label and the ICD long title, so no other Coding gets display
    text that no source provided.
    """
    node = BNode()
    g.add((node, FHIR["Coding.system"], uri(system)))
    g.add((node, FHIR["Coding.code"], Literal(code)))
    if display is not None:
        g.add((node, FHIR["Coding.display"], Literal(display)))
    return node


def codeable_concept(g, codings):
    """Return a CodeableConcept blank node with one Coding per (system, code[, display]) tuple.

    All Codings in one CodeableConcept express the same concept in different
    code systems (e.g. MICU as HL7 "ICU" plus the more specific SNOMED code).
    Separate concepts need separate CodeableConcepts (e.g. Neuro SICU's "ICU"
    and "NS"), which is why the mapping tables nest codings as lists of lists.
    Coding order is not recorded, because the simplified dialect omits fhir:index (D7).
    """
    node = BNode()
    for c in codings:
        g.add((node, FHIR["CodeableConcept.coding"], coding(g, *c)))
    return node


def identifier(g, system, value):
    """Return an Identifier blank node pairing a source ID with its system.

    This is where MIMIC IDs are recorded as data (model §3.1); IRIs only use
    them as part of a name.
    """
    node = BNode()
    g.add((node, FHIR["Identifier.system"], uri(system)))
    g.add((node, FHIR["Identifier.value"], Literal(value)))
    return node


def period(g, start, end):
    """Return a Period blank node with both start and end.

    Every encounter here is finished, so both ends must exist. A missing end
    makes date_time() raise an error rather than producing an open-ended period.
    """
    node = BNode()
    g.add((node, FHIR["Period.start"], date_time(start)))
    g.add((node, FHIR["Period.end"], date_time(end)))
    return node


def extension(g, url, predicate, value):
    """Return an Extension blank node with its url and one value.

    FHIR builds the value's type into the property name (valueBoolean,
    valueString), so the caller passes that name explicitly rather than having
    it inferred from the Python value.
    """
    node = BNode()
    g.add((node, FHIR["Extension.url"], uri(url)))
    g.add((node, FHIR[predicate], value))
    return node


# =============================================================================
# Resource builders: one function per resource kind, each a flat list of
# g.add() calls that mirrors its branch of the model's diagram so the two can
# be checked side by side. Builders only translate the rows they are given;
# the pipeline below finds and matches rows across tables. Quoted constants
# ("final", "finished", "IMP", ...) are model policy, not source data.
# =============================================================================

def add_patient(g, subject_id):
    """Add a Patient carrying only its MIMIC identifier (model §7.1).

    Patients have no source table of their own; the pipeline derives them from
    the admissions. The model defines nothing else about patients in scope.
    """
    iri = patient_iri(subject_id)
    g.add((iri, RDF.type, FHIR.Patient))
    g.add((iri, FHIR["Patient.identifier"], identifier(g, ID_PATIENT, subject_id)))


def add_location(g, careunit):
    """Add one Location per care-unit kind (model §9).

    mode "kind" means a type of unit, not a specific ward, so every interval
    in that unit references this single resource. Each entry in
    CARE_UNIT_TYPES[careunit] becomes a separate Location.type.
    """
    iri = location_iri(careunit)
    g.add((iri, RDF.type, FHIR.Location))
    g.add((iri, FHIR["Location.mode"], Literal("kind")))
    g.add((iri, FHIR["Location.name"], Literal(careunit)))
    for codings in CARE_UNIT_TYPES[careunit]:
        g.add((iri, FHIR["Location.type"], codeable_concept(g, codings)))


def add_hospital_encounter(g, row, diagnosis):
    """Add a Hospital Encounter with its first-ranked diagnosis (model §7.3, §8, §10.2).

    The verbatim admission_type extension is written for every encounter,
    because the priority mapping loses detail (EW EMER. and DIRECT EMER. both
    become EM) and must not replace the source value. Priority is written only
    where an approved mapping exists; RDF has no null, so an unmapped type has
    no priority triple at all. The diagnosis row comes from another table, so
    the pipeline passes it in. Encounter.diagnosis is a blank node because rank
    and role describe the condition's role in this particular stay.
    """
    iri = hospital_encounter_iri(row["hadm_id"])
    g.add((iri, RDF.type, FHIR.Encounter))
    g.add((iri, FHIR["Encounter.identifier"], identifier(g, ID_ENCOUNTER_HOSP, row["hadm_id"])))
    g.add((iri, FHIR["Encounter.status"], Literal("finished")))
    g.add((iri, FHIR["Encounter.class"], coding(g, ACT_CODE, "IMP")))
    priority = lookup(ADMISSION_PRIORITY, row["admission_type"], "admission_type")
    if priority is not None:
        g.add((iri, FHIR["Encounter.priority"], codeable_concept(g, [(ACT_PRIORITY, priority)])))
    g.add((iri, FHIR["DomainResource.extension"],
           extension(g, EXT_ADMISSION_TYPE, "Extension.valueString", Literal(row["admission_type"]))))
    g.add((iri, FHIR["Encounter.subject"], patient_iri(row["subject_id"])))
    g.add((iri, FHIR["Encounter.period"], period(g, row["admittime"], row["dischtime"])))

    dx = BNode()
    g.add((dx, FHIR["Encounter.diagnosis.condition"], condition_iri(diagnosis["hadm_id"])))
    g.add((dx, FHIR["Encounter.diagnosis.use"], codeable_concept(g, [(DIAGNOSIS_ROLE, "billing")])))
    g.add((dx, FHIR["Encounter.diagnosis.rank"],
           Literal(diagnosis["seq_num"], datatype=XSD.positiveInteger, normalize=False)))
    g.add((iri, FHIR["Encounter.diagnosis"], dx))


def add_condition(g, row):
    """Add the Condition for an admission's first-ranked billed diagnosis (model §10).

    Condition.code keeps the raw MIMIC code with long_title as display, plus
    the canonical dotted ICD code; neither replaces the other. Condition.encounter
    links back to the encounter, so queries can start from either side.
    """
    source_system, canonical_system = lookup(ICD_SYSTEMS, row["icd_version"], "icd_version")
    iri = condition_iri(row["hadm_id"])
    g.add((iri, RDF.type, FHIR.Condition))
    g.add((iri, FHIR["Condition.subject"], patient_iri(row["subject_id"])))
    g.add((iri, FHIR["Condition.encounter"], hospital_encounter_iri(row["hadm_id"])))
    g.add((iri, FHIR["Condition.category"],
           codeable_concept(g, [(CONDITION_CATEGORY, "encounter-diagnosis")])))
    g.add((iri, FHIR["Condition.code"], codeable_concept(g, [
        (source_system, row["icd_code"], row["long_title"]),
        (canonical_system, canonical_icd(row["icd_code"], row["icd_version"])),
    ])))


def add_icu_encounter(g, row, intervals):
    """Add an ICU Encounter with its care-unit intervals (model §7.2, §9.1).

    Each interval becomes an Encounter.location blank node with its own period,
    referencing the shared Location for that care unit. transfer_id and
    eventtype are deliberately omitted (model §11).
    """
    iri = icu_encounter_iri(row["stay_id"])
    g.add((iri, RDF.type, FHIR.Encounter))
    g.add((iri, FHIR["Encounter.identifier"], identifier(g, ID_ENCOUNTER_ICU, row["stay_id"])))
    g.add((iri, FHIR["Encounter.status"], Literal("finished")))
    g.add((iri, FHIR["Encounter.class"], coding(g, ACT_CODE, "ACUTE")))
    g.add((iri, FHIR["Encounter.subject"], patient_iri(row["subject_id"])))
    g.add((iri, FHIR["Encounter.period"], period(g, row["intime"], row["outtime"])))
    g.add((iri, FHIR["Encounter.partOf"], hospital_encounter_iri(row["hadm_id"])))
    # transfer_id and eventtype are deliberately not represented (model §11).
    for interval in intervals:
        loc = BNode()
        g.add((loc, FHIR["Encounter.location.period"], period(g, interval["intime"], interval["outtime"])))
        g.add((loc, FHIR["Encounter.location.location"], location_iri(interval["careunit"])))
        g.add((iri, FHIR["Encounter.location"], loc))


def add_observation(g, row):
    """Add one Observation for a source row (model §5, §6).

    Before building, the row's label and unit must match the item table: the
    UCUM code is chosen by itemid, so a row with an unexpected unit would
    otherwise get a wrong normalisation. A duplicate IRI also raises an error,
    because RDF would silently merge the two rows (see observation_iri).
    """
    item = lookup(ITEMS, row["itemid"], "itemid")
    if row["measurement_label"] != item["label"]:
        raise ValueError(f"itemid {row['itemid']} has unexpected label {row['measurement_label']!r}")
    if row["valueuom"] != item["unit"]:
        raise ValueError(f"itemid {row['itemid']} has unexpected unit {row['valueuom']!r}")

    iri = observation_iri(row["stay_id"], row["charttime"], row["itemid"])
    if (iri, RDF.type, FHIR.Observation) in g:
        raise ValueError(f"duplicate observation key: {iri}")
    g.add((iri, RDF.type, FHIR.Observation))
    g.add((iri, FHIR["Observation.status"], Literal("final")))
    g.add((iri, FHIR["Observation.category"], codeable_concept(g, [(OBSERVATION_CATEGORY, "vital-signs")])))
    g.add((iri, FHIR["Observation.code"], codeable_concept(
        g, [(CS_MIMIC_ITEMS, row["itemid"], row["measurement_label"])] + [(LOINC, c) for c in item["loinc"]])))
    g.add((iri, FHIR["Observation.subject"], patient_iri(row["subject_id"])))
    g.add((iri, FHIR["Observation.effectiveDateTime"], date_time(row["charttime"])))

    quantity = BNode()
    g.add((quantity, FHIR["Quantity.value"], decimal(row["valuenum"])))
    g.add((quantity, FHIR["Quantity.unit"], Literal(row["valueuom"])))
    g.add((quantity, FHIR["Quantity.system"], uri(UCUM)))
    g.add((quantity, FHIR["Quantity.code"], Literal(item["ucum"])))
    g.add((iri, FHIR["Observation.valueQuantity"], quantity))

    warning = lookup(WARNING, row["warning"], "warning")
    g.add((iri, FHIR["DomainResource.extension"],
           extension(g, EXT_WARNING, "Extension.valueBoolean", Literal(warning))))
    g.add((iri, FHIR["Observation.encounter"], icu_encounter_iri(row["stay_id"])))


# =============================================================================
# Pipeline: the only code that reads files and matches rows across tables.
# build_graph() checks that the tables agree before building anything, and
# main() writes the output only after a successful build, so bad source data
# stops the run without leaving a partial or overwritten Turtle file.
# =============================================================================

def read_table(source, name):
    """Return a table's rows as dicts of exact source strings.

    csv is used rather than pandas so no value is type-converted (IDs stay
    text, "91.0" stays "91.0"). Encoding and newline handling are explicit so
    every machine reads the file identically.
    """
    with open(source / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def unique_index(rows, key, table):
    """Return rows indexed by key, raising ValueError on a duplicate key.

    A plain dict comprehension would silently keep only the last duplicate,
    dropping a resource from the RDF without warning.
    """
    index = {}
    for row in rows:
        if row[key] in index:
            raise ValueError(f"duplicate {key} {row[key]} in {table}")
        index[row[key]] = row
    return index


def check_link(row, parent, fields, context):
    """Raise ValueError if a row's copies of its parent's keys disagree with the parent.

    The tables repeat parent keys, and the RDF uses different copies in
    different places (e.g. Observation.subject from the observation row,
    Observation.encounter via the stay). Taking the parent's value instead would
    quietly repair the source; checking reports the disagreement.
    """
    for field in fields:
        if row[field] != parent[field]:
            raise ValueError(f"{context}: {field} {row[field]} disagrees with parent {parent[field]}")


def build_graph(source=DEFAULT_SOURCE):
    """Read the source tables, check they agree, and return the RDF graph.

    All checks run before any triple is added. They cover only what the
    builders rely on: unique keys, matching parent links, exactly one seq_num 1
    diagnosis per admission, and approved care units. Extraction properties
    such as the four-hour window are validated in the notebook. Sorting makes
    the build order identical on every run but does not change the graph.
    Kept separate from main() so tests can build a graph in memory.
    """
    source = Path(source)
    admissions = unique_index(read_table(source, "hospital_admissions"), "hadm_id", "hospital_admissions")
    diagnoses = unique_index(read_table(source, "first_ranked_diagnoses"), "hadm_id", "first_ranked_diagnoses")
    stays = unique_index(read_table(source, "icu_stays"), "stay_id", "icu_stays")
    intervals = read_table(source, "careunit_intervals")
    observations = read_table(source, "observations")

    # Relational integrity checks; the source tables are never modified.
    if set(diagnoses) != set(admissions):
        raise ValueError("first-ranked diagnoses do not cover exactly the represented admissions")
    for dx in diagnoses.values():
        if dx["seq_num"] != "1":
            raise ValueError(f"diagnosis for hadm_id {dx['hadm_id']} is not seq_num 1")
        check_link(dx, admissions[dx["hadm_id"]], ["subject_id"], "first_ranked_diagnoses")
    for stay in stays.values():
        check_link(stay, lookup(admissions, stay["hadm_id"], "icu_stays.hadm_id"), ["subject_id"], "icu_stays")
    intervals_by_stay = {}
    for interval in intervals:
        lookup(CARE_UNIT_TYPES, interval["careunit"], "careunit")
        stay = lookup(stays, interval["stay_id"], "careunit_intervals.stay_id")
        check_link(interval, stay, ["subject_id", "hadm_id"], "careunit_intervals")
        intervals_by_stay.setdefault(interval["stay_id"], []).append(interval)
    for obs in observations:
        stay = lookup(stays, obs["stay_id"], "observations.stay_id")
        check_link(obs, stay, ["subject_id", "hadm_id"], "observations")

    g = Graph()
    g.bind("fhir", FHIR)
    g.bind("data", DATA)
    g.bind("xsd", XSD)

    for subject_id in sorted({row["subject_id"] for row in admissions.values()}):
        add_patient(g, subject_id)
    for careunit in sorted({row["careunit"] for row in intervals}):
        add_location(g, careunit)
    for hadm_id in sorted(admissions):
        add_hospital_encounter(g, admissions[hadm_id], diagnoses[hadm_id])
        add_condition(g, diagnoses[hadm_id])
    for stay_id in sorted(stays):
        # Sorting has no effect on the graph: RDF stores the intervals as an unordered
        # set, and each one's period carries its own times. It only shows that the
        # care-unit history is chronological (it would matter if fhir:index were used).
        stay_intervals = sorted(intervals_by_stay.get(stay_id, []), key=lambda r: r["intime"])
        add_icu_encounter(g, stays[stay_id], stay_intervals)
    for obs in observations:
        add_observation(g, obs)
    return g


def main():
    """Command-line entry point: build the graph, then write it as Turtle."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="canonical source table directory")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Turtle output path")
    args = parser.parse_args()

    g = build_graph(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=args.output, format="turtle", encoding="utf-8")
    print(f"Wrote {len(g)} triples to {args.output}")


if __name__ == "__main__":
    main()
