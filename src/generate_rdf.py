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


# --- IRI minting (D2) ---

def patient_iri(subject_id):
    return DATA[f"patient-{subject_id}"]


def hospital_encounter_iri(hadm_id):
    return DATA[f"hospital-encounter-{hadm_id}"]


def icu_encounter_iri(stay_id):
    return DATA[f"icu-encounter-{stay_id}"]


def condition_iri(hadm_id):
    return DATA[f"condition-{hadm_id}"]


def observation_iri(stay_id, charttime, itemid):
    stamp = charttime.replace("-", "").replace(":", "").replace(" ", "T")
    return DATA[f"observation-{stay_id}-{stamp}-{itemid}"]


def location_iri(careunit):
    slug = re.sub(r"[^a-z0-9]+", "-", careunit.lower()).strip("-")
    return DATA[f"location-{slug}"]


# --- Literal helpers ---

def lookup(table, key, field):
    if key not in table:
        raise ValueError(f"{field} value {key!r} is outside the approved mapping")
    return table[key]


def uri(value):
    return Literal(value, datatype=XSD.anyURI)


def date_time(value):
    if not TIMESTAMP.match(value):
        raise ValueError(f"unexpected timestamp format: {value!r}")
    return Literal(value.replace(" ", "T"), datatype=XSD.dateTime, normalize=False)


def decimal(value):
    if not DECIMAL.match(value):
        raise ValueError(f"unexpected numeric value: {value!r}")
    return Literal(value, datatype=XSD.decimal, normalize=False)


def canonical_icd(code, version):
    """Insert the standard ICD-9-CM / ICD-10-CM decimal point without otherwise changing the code."""
    if not ICD_CODE.match(code):
        raise ValueError(f"unexpected ICD code: {code!r}")
    lookup(ICD_SYSTEMS, version, "icd_version")
    # ICD-9-CM E-codes carry four characters before the decimal; all other codes carry three.
    split = 4 if version == "9" and code.startswith("E") else 3
    return code if len(code) <= split else f"{code[:split]}.{code[split:]}"


# --- Datatype builders (all nested elements are blank nodes, D3) ---

def coding(g, system, code, display=None):
    node = BNode()
    g.add((node, FHIR["Coding.system"], uri(system)))
    g.add((node, FHIR["Coding.code"], Literal(code)))
    if display is not None:
        g.add((node, FHIR["Coding.display"], Literal(display)))
    return node


def codeable_concept(g, codings):
    node = BNode()
    for c in codings:
        g.add((node, FHIR["CodeableConcept.coding"], coding(g, *c)))
    return node


def identifier(g, system, value):
    node = BNode()
    g.add((node, FHIR["Identifier.system"], uri(system)))
    g.add((node, FHIR["Identifier.value"], Literal(value)))
    return node


def period(g, start, end):
    node = BNode()
    g.add((node, FHIR["Period.start"], date_time(start)))
    g.add((node, FHIR["Period.end"], date_time(end)))
    return node


def extension(g, url, predicate, value):
    node = BNode()
    g.add((node, FHIR["Extension.url"], uri(url)))
    g.add((node, FHIR[predicate], value))
    return node


# --- Resource builders ---

def add_patient(g, subject_id):
    iri = patient_iri(subject_id)
    g.add((iri, RDF.type, FHIR.Patient))
    g.add((iri, FHIR["Patient.identifier"], identifier(g, ID_PATIENT, subject_id)))


def add_location(g, careunit):
    iri = location_iri(careunit)
    g.add((iri, RDF.type, FHIR.Location))
    g.add((iri, FHIR["Location.mode"], Literal("kind")))
    g.add((iri, FHIR["Location.name"], Literal(careunit)))
    for codings in CARE_UNIT_TYPES[careunit]:
        g.add((iri, FHIR["Location.type"], codeable_concept(g, codings)))


def add_hospital_encounter(g, row, diagnosis):
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


# --- Pipeline ---

def read_table(source, name):
    with open(source / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def unique_index(rows, key, table):
    index = {}
    for row in rows:
        if row[key] in index:
            raise ValueError(f"duplicate {key} {row[key]} in {table}")
        index[row[key]] = row
    return index


def check_link(row, parent, fields, context):
    for field in fields:
        if row[field] != parent[field]:
            raise ValueError(f"{context}: {field} {row[field]} disagrees with parent {parent[field]}")


def build_graph(source=DEFAULT_SOURCE):
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
        stay_intervals = sorted(intervals_by_stay.get(stay_id, []), key=lambda r: r["intime"])
        add_icu_encounter(g, stays[stay_id], stay_intervals)
    for obs in observations:
        add_observation(g, obs)
    return g


def main():
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
