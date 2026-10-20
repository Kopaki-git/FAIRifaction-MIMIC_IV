"""Acceptance checks for rdf/mimic_icu_vitals_4h.ttl (docs/rdf_implementation_handoff.md §6).

Expected mappings below are transcribed independently from docs/semantic_model_mapping.md rather
than imported from the generator, so transcription errors in either place surface as failures.
Passing these checks establishes RDF syntax, source fidelity, relational integrity and mapping
fidelity. It does not establish strict FHIR-RDF serialization or FHIR instance conformance.
"""

import csv
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pyoxigraph
import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import generate_rdf as gen  # noqa: E402

TTL = ROOT / "rdf" / "mimic_icu_vitals_4h.ttl"
SOURCE = ROOT / "data" / "derived" / "mimic_icu_vitals_4h"

F = Namespace("http://hl7.org/fhir/")
DATA = Namespace("https://w3id.org/FAIR-course-UT/2026-2027/group4/data#")
EXT_BASE = "https://w3id.org/FAIR-course-UT/2026-2027/group4/fhir/StructureDefinition/"
MIMIC = "http://mimic.mit.edu/fhir/mimic/"
HL7 = "http://terminology.hl7.org/CodeSystem/"
LOINC = "http://loinc.org"
SNOMED = "http://snomed.info/sct"

# Model §6.1 / §6.2.
EXPECTED_ITEMS = {
    "220045": ({"8867-4"}, "bpm", "/min"),
    "220210": ({"9279-1"}, "insp/min", "/min"),
    "220277": ({"2708-6", "59408-5"}, "%", "%"),
}
# Model §8.2.
EXPECTED_PRIORITY = {
    "ELECTIVE": "EL", "URGENT": "UR", "EW EMER.": "EM", "DIRECT EMER.": "EM",
    "OBSERVATION ADMIT": None, "SURGICAL SAME DAY ADMISSION": None,
}
# Model §9.2 / §9.3: one frozenset of (system, code) per Location.type CodeableConcept.
ROLE = HL7 + "v3-RoleCode"
EXPECTED_LOCATION_TYPES = {
    "Medical Intensive Care Unit (MICU)": {frozenset({(ROLE, "ICU"), (SNOMED, "441994008")})},
    "Surgical Intensive Care Unit (SICU)": {frozenset({(ROLE, "ICU"), (SNOMED, "418433008")})},
    "Medical/Surgical Intensive Care Unit (MICU/SICU)": {frozenset({(ROLE, "ICU")})},
    "Trauma SICU (TSICU)": {frozenset({(ROLE, "ICU")})},
    "Neuro Surgical Intensive Care Unit (Neuro SICU)": {frozenset({(ROLE, "ICU")}), frozenset({(ROLE, "NS")})},
    "Neuro Stepdown": {frozenset({(ROLE, "HU")})},
    "Cardiac Vascular Intensive Care Unit (CVICU)": {frozenset({(ROLE, "ICU")})},
    "Coronary Care Unit (CCU)": {frozenset({(ROLE, "CCU")})},
    "Neuro Intermediate": {frozenset({(ROLE, "HU")})},
}
# Model §10.3.
EXPECTED_ICD_SYSTEMS = {
    "9": (MIMIC + "CodeSystem/mimic-diagnosis-icd9", "http://hl7.org/fhir/sid/icd-9-cm"),
    "10": (MIMIC + "CodeSystem/mimic-diagnosis-icd10", "http://hl7.org/fhir/sid/icd-10-cm"),
}


# =============================================================================
# Fixtures and helpers. Independence rule: nothing here takes expected values
# from the generator. src reads the CSVs itself instead of calling
# gen.read_table(), and iso() restates the timestamp rule instead of calling
# gen.date_time(), so a generator bug cannot be copied into what the tests expect.
# =============================================================================

@pytest.fixture(scope="module")
def g():
    """Return the committed Turtle graph, parsed once and shared, so tests must only read it."""
    return Graph().parse(TTL, format="turtle")


@pytest.fixture(scope="module")
def src():
    """Return the five source tables as lists of dicts of exact strings.

    Module-scoped: read once and shared by every test in this file, so tests
    must only read these rows and never modify them. One test changing a row
    would silently change the source data that every later test sees.
    """
    def read(name):
        with open(SOURCE / f"{name}.csv", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return {name: read(name) for name in [
        "observations", "icu_stays", "careunit_intervals", "hospital_admissions", "first_ranked_diagnoses"]}


def one(g, s, p):
    """Return the single object of (s, p), failing the test if there are none or several.

    Unlike rdflib's g.value(), which silently returns an arbitrary value when
    there are several, this makes every field a test reads also a check that
    the value is neither missing nor duplicated.
    """
    objects = list(g.objects(s, p))
    assert len(objects) == 1, f"{s} {p}: expected exactly one value, found {len(objects)}"
    return objects[0]


def codings(g, cc):
    return frozenset((str(one(g, c, F["Coding.system"])), str(one(g, c, F["Coding.code"])))
                     for c in g.objects(cc, F["CodeableConcept.coding"]))


def single_coding(g, node):
    return str(one(g, node, F["Coding.system"])), str(one(g, node, F["Coding.code"]))


def period(g, node):
    return str(one(g, node, F["Period.start"])), str(one(g, node, F["Period.end"]))


def iso(ts):
    return ts.replace(" ", "T")


def identifier(g, s, p):
    node = one(g, s, p)
    return str(one(g, node, F["Identifier.system"])), str(one(g, node, F["Identifier.value"]))


def extensions(g, s):
    return {str(one(g, e, F["Extension.url"])): e for e in g.objects(s, F["DomainResource.extension"])}


def typed(g, rdf_type):
    return set(g.subjects(RDF.type, rdf_type))


# =============================================================================
# Parsing and counts (handoff §6): the broadest checks. Counts are fixed numbers
# from the dataset invariants in AGENTS.md, not computed from the CSVs, so they
# also catch the source drifting from what was documented. Counts catch
# resources that are missing, extra or merged; whether each resource is
# correct is left to the per-resource tests below.
# =============================================================================

# --- 1. Parsing ---

def test_parses_with_independent_parser(g):
    """Parse the committed Turtle with Oxigraph and compare its triple count with RDFLib's.

    RDFLib both wrote the file and (in the g fixture) read it back, so a quirk
    in its writer could be accepted by its own reader. Oxigraph is a separate,
    strict, Rust-based implementation. If both parse the file and agree on a non-zero count,
    it is standard Turtle and neither parser skipped statements.
    """
    triples = list(pyoxigraph.parse(path=str(TTL), format=pyoxigraph.RdfFormat.TURTLE))
    assert len(triples) == len(g) > 0


# --- 2. Resource and interval counts ---

def test_resource_counts(g):
    """Count each resource kind against the dataset invariants.

    Resources are counted as distinct typed subjects, so two rows merged into
    one IRI would lower the count. Encounters are counted per class (ACUTE for
    ICU stays, IMP for hospital admissions) because both share fhir:Encounter.
    Care-unit intervals are blank nodes, so they are counted as objects of
    Encounter.location. Misclassifications that offset each other would cancel
    out here; the per-resource tests check each encounter's class individually.
    """
    assert len(typed(g, F.Observation)) == 2501
    assert len(typed(g, F.Patient)) == 94
    assert len(typed(g, F.Condition)) == 121
    assert len(typed(g, F.Location)) == 9
    classes = Counter(single_coding(g, one(g, e, F["Encounter.class"]))[1] for e in typed(g, F.Encounter))
    assert classes == {"ACUTE": 133, "IMP": 121}
    assert len(list(g.objects(None, F["Encounter.location"]))) == 167


def test_loinc_counts(g):
    """Count LOINC codings across all Observations against the expected totals per code.

    Heart rate and respiratory rate carry one LOINC code each, and every SpO2
    row carries both 2708-6 and 59408-5 (dual coding). Codings are collected
    per Observation as a set, so a Coding duplicated within one Observation
    would be counted once. This is a known, accepted gap; the per-resource tests
    compare sets too.
    """
    loinc = Counter()
    for obs in typed(g, F.Observation):
        for system, code in codings(g, one(g, obs, F["Observation.code"])):
            if system == LOINC:
                loinc[code] += 1
    assert loinc == {"8867-4": 859, "9279-1": 860, "2708-6": 782, "59408-5": 782}


# =============================================================================
# Per-resource tests (handoff §6 criteria 3-5). Each test loops over one source
# table, rebuilds the expected IRI for each row by hand, reads every field
# through one() and compares it with the row. With the counts above, this gives
# an exact one-to-one match between source rows and resources. A test stops at
# its first failing row, so only one failure is shown at a time.
# =============================================================================

# --- 3-5. References, source fidelity and codings, per resource kind ---

def test_observations_match_source(g, src):
    """Check every Observation against its source row.

    Covers status, category, subject and ICU encounter references, the typed
    charttime, the MIMIC and LOINC codes with the MIMIC display, the quantity
    (decimal type, numeric value, source unit, UCUM system and code) and the
    warning extension as the only extension.
    """
    rows = src["observations"]
    assert len(rows) == 2501
    for row in rows:
        stamp = row["charttime"].replace("-", "").replace(":", "").replace(" ", "T")
        obs = DATA[f"observation-{row['stay_id']}-{stamp}-{row['itemid']}"]
        assert (obs, RDF.type, F.Observation) in g
        assert one(g, obs, F["Observation.status"]) == Literal("final")
        assert one(g, obs, F["Observation.subject"]) == DATA[f"patient-{row['subject_id']}"]
        assert one(g, obs, F["Observation.encounter"]) == DATA[f"icu-encounter-{row['stay_id']}"]
        assert one(g, obs, F["Observation.effectiveDateTime"]) == Literal(iso(row["charttime"]), datatype=XSD.dateTime)
        assert codings(g, one(g, obs, F["Observation.category"])) == {(HL7 + "observation-category", "vital-signs")}

        loinc, unit, ucum = EXPECTED_ITEMS[row["itemid"]]
        code = one(g, obs, F["Observation.code"])
        assert codings(g, code) == {(MIMIC + "CodeSystem/mimic-chartevents-d-items", row["itemid"])} | {
            (LOINC, c) for c in loinc}
        mimic_coding = [c for c in g.objects(code, F["CodeableConcept.coding"])
                        if str(one(g, c, F["Coding.system"])).startswith(MIMIC)]
        assert one(g, mimic_coding[0], F["Coding.display"]) == Literal(row["measurement_label"])

        q = one(g, obs, F["Observation.valueQuantity"])
        value = one(g, q, F["Quantity.value"])
        assert value.datatype == XSD.decimal and Decimal(str(value)) == Decimal(row["valuenum"])
        assert one(g, q, F["Quantity.unit"]) == Literal(row["valueuom"]) and row["valueuom"] == unit
        assert str(one(g, q, F["Quantity.system"])) == "http://unitsofmeasure.org"
        assert one(g, q, F["Quantity.code"]) == Literal(ucum)

        ext = extensions(g, obs)
        assert set(ext) == {EXT_BASE + "observation-mimic-warning"}
        flag = one(g, ext[EXT_BASE + "observation-mimic-warning"], F["Extension.valueBoolean"])
        assert flag == Literal({"0": False, "1": True}[row["warning"]])


def test_values_keep_source_lexical_form(src):
    """Check that every value and charttime keeps its exact source text in the file.

    Numerically "91.0" equals "91", but FHIR treats them as different precisions.
    RDFLib and pyoxigraph.Store rewrite such values when loading, so this reads
    the file with pyoxigraph's streaming parser, which keeps the text as written.
    """
    # The pyoxigraph parser (unlike rdflib and pyoxigraph.Store) keeps literals' lexical form,
    # so this checks the serialized text itself.
    quantity, value, time = {}, {}, {}
    for t in pyoxigraph.parse(path=str(TTL), format=pyoxigraph.RdfFormat.TURTLE):
        p = t.predicate.value
        if p == str(F["Observation.valueQuantity"]):
            quantity[t.subject.value] = t.object
        elif p == str(F["Quantity.value"]):
            value[t.subject] = t.object.value
        elif p == str(F["Observation.effectiveDateTime"]):
            time[t.subject.value] = t.object.value
    found = {obs: (value[q], time[obs]) for obs, q in quantity.items()}
    assert len(found) == 2501
    for row in src["observations"]:
        stamp = row["charttime"].replace("-", "").replace(":", "").replace(" ", "T")
        iri = str(DATA[f"observation-{row['stay_id']}-{stamp}-{row['itemid']}"])
        assert found[iri] == (row["valuenum"], iso(row["charttime"]))


def test_icu_encounters_match_source(g, src):
    """Check every ICU Encounter against icu_stays and its care-unit intervals.

    Covers identifier, status, class ACUTE, subject, partOf the hospital
    encounter and period, and checks that its Encounter.location entries match
    the source intervals exactly: times, Location reference and that Location's name.
    """
    intervals = {}
    for row in src["careunit_intervals"]:
        intervals.setdefault(row["stay_id"], set()).add(
            (iso(row["intime"]), iso(row["outtime"]), gen.location_iri(row["careunit"]), row["careunit"]))
    for row in src["icu_stays"]:
        enc = DATA[f"icu-encounter-{row['stay_id']}"]
        assert (enc, RDF.type, F.Encounter) in g
        assert identifier(g, enc, F["Encounter.identifier"]) == (MIMIC + "identifier/encounter-icu", row["stay_id"])
        assert one(g, enc, F["Encounter.status"]) == Literal("finished")
        assert single_coding(g, one(g, enc, F["Encounter.class"])) == (HL7 + "v3-ActCode", "ACUTE")
        assert one(g, enc, F["Encounter.subject"]) == DATA[f"patient-{row['subject_id']}"]
        assert one(g, enc, F["Encounter.partOf"]) == DATA[f"hospital-encounter-{row['hadm_id']}"]
        assert period(g, one(g, enc, F["Encounter.period"])) == (iso(row["intime"]), iso(row["outtime"]))

        actual = set()
        for loc in g.objects(enc, F["Encounter.location"]):
            target = one(g, loc, F["Encounter.location.location"])
            start, end = period(g, one(g, loc, F["Encounter.location.period"]))
            actual.add((start, end, target, str(one(g, target, F["Location.name"]))))
        assert actual == intervals[row["stay_id"]]


def test_hospital_encounters_match_source(g, src):
    """Check every Hospital Encounter against hospital_admissions.

    Covers identifier, status, class IMP, subject, period, the absence of
    partOf, the verbatim admission_type as the only extension, and the diagnosis
    (condition, rank 1, use billing). Priority must match the mapping exactly;
    for the two unmapped types it must be absent, so an invented priority fails.
    """
    for row in src["hospital_admissions"]:
        enc = DATA[f"hospital-encounter-{row['hadm_id']}"]
        assert (enc, RDF.type, F.Encounter) in g
        assert identifier(g, enc, F["Encounter.identifier"]) == (MIMIC + "identifier/encounter-hosp", row["hadm_id"])
        assert one(g, enc, F["Encounter.status"]) == Literal("finished")
        assert single_coding(g, one(g, enc, F["Encounter.class"])) == (HL7 + "v3-ActCode", "IMP")
        assert one(g, enc, F["Encounter.subject"]) == DATA[f"patient-{row['subject_id']}"]
        assert period(g, one(g, enc, F["Encounter.period"])) == (iso(row["admittime"]), iso(row["dischtime"]))
        assert list(g.objects(enc, F["Encounter.partOf"])) == []

        ext = extensions(g, enc)
        assert set(ext) == {EXT_BASE + "encounter-mimic-admission-type"}
        assert one(g, ext[EXT_BASE + "encounter-mimic-admission-type"], F["Extension.valueString"]) == Literal(
            row["admission_type"])

        expected = EXPECTED_PRIORITY[row["admission_type"]]
        priorities = [codings(g, p) for p in g.objects(enc, F["Encounter.priority"])]
        assert priorities == ([] if expected is None else [{(HL7 + "v3-ActPriority", expected)}])

        dx = one(g, enc, F["Encounter.diagnosis"])
        assert one(g, dx, F["Encounter.diagnosis.condition"]) == DATA[f"condition-{row['hadm_id']}"]
        assert one(g, dx, F["Encounter.diagnosis.rank"]) == Literal("1", datatype=XSD.positiveInteger)
        assert codings(g, one(g, dx, F["Encounter.diagnosis.use"])) == {(HL7 + "diagnosis-role", "billing")}


def test_conditions_match_source(g, src):
    """Check every Condition against first_ranked_diagnoses.

    Covers subject, encounter, category and the two ICD codings: the raw source
    code with long_title as display, and the canonical code. The canonical code
    is checked structurally (the raw code with only a dot inserted), not
    against an ICD release.
    """
    for row in src["first_ranked_diagnoses"]:
        cond = DATA[f"condition-{row['hadm_id']}"]
        assert (cond, RDF.type, F.Condition) in g
        assert one(g, cond, F["Condition.subject"]) == DATA[f"patient-{row['subject_id']}"]
        assert one(g, cond, F["Condition.encounter"]) == DATA[f"hospital-encounter-{row['hadm_id']}"]
        assert codings(g, one(g, cond, F["Condition.category"])) == {
            (HL7 + "condition-category", "encounter-diagnosis")}

        source_system, canonical_system = EXPECTED_ICD_SYSTEMS[row["icd_version"]]
        code = one(g, cond, F["Condition.code"])
        actual = codings(g, code)
        assert len(actual) == 2
        assert (source_system, row["icd_code"]) in actual
        canonical = [c for s, c in actual if s == canonical_system]
        assert len(canonical) == 1
        # Canonical form differs from the raw code only by an inserted decimal point.
        assert canonical[0].replace(".", "") == row["icd_code"] and canonical[0].count(".") <= 1
        source_coding = [c for c in g.objects(code, F["CodeableConcept.coding"])
                         if str(one(g, c, F["Coding.system"])) == source_system]
        assert one(g, source_coding[0], F["Coding.display"]) == Literal(row["long_title"])


def test_patients_match_source(g, src):
    """Check that each of the 94 patients has its MIMIC identifier and system."""
    subject_ids = {row["subject_id"] for row in src["hospital_admissions"]}
    assert len(subject_ids) == 94
    for subject_id in subject_ids:
        patient = DATA[f"patient-{subject_id}"]
        assert identifier(g, patient, F["Patient.identifier"]) == (MIMIC + "identifier/patient", subject_id)


def test_locations_match_frozen_mapping(g, src):
    """Check the care-unit Locations against the frozen mapping (model §9).

    The source must contain exactly the nine mapped care units, and each
    Location must have mode "kind" and exactly the expected Location.type
    groupings. The documented example IRI is pinned as well, because the ICU
    encounter test computes Location IRIs with the generator's own location_iri().
    """
    careunits = {row["careunit"] for row in src["careunit_intervals"]}
    assert careunits == set(EXPECTED_LOCATION_TYPES)
    for loc in typed(g, F.Location):
        name = str(one(g, loc, F["Location.name"]))
        assert one(g, loc, F["Location.mode"]) == Literal("kind")
        assert {codings(g, t) for t in g.objects(loc, F["Location.type"])} == EXPECTED_LOCATION_TYPES[name]
        assert len(list(g.objects(loc, F["Location.type"]))) == len(EXPECTED_LOCATION_TYPES[name])
    # Documented example IRI (docs/rdf_serialization.md, D2), written out rather than computed.
    assert one(g, DATA["location-medical-intensive-care-unit-micu"], F["Location.name"]) == Literal(
        "Medical Intensive Care Unit (MICU)")


def test_references_resolve(g):
    """Check that every reference points at an IRI that is a typed resource in the graph.

    It confirms that the targets exist, not that they are the right kind of
    resource; the per-resource tests above check that.
    """
    reference_predicates = [
        "Observation.subject", "Observation.encounter", "Encounter.subject", "Encounter.partOf",
        "Encounter.location.location", "Encounter.diagnosis.condition", "Condition.subject", "Condition.encounter"]
    for p in reference_predicates:
        for target in g.objects(None, F[p]):
            assert isinstance(target, URIRef) and (target, RDF.type, None) in g, f"{p} -> {target}"


# =============================================================================
# Edge cases (handoff §6 criterion 7). Most re-check cases the per-resource
# tests already cover, but give each one a named test for the report. Each
# first asserts that its case exists in the data, so it cannot pass vacuously.
# test_canonical_icd_formatting and test_unapproved_source_values_fail are the
# only tests that call generator functions directly rather than read the output.
# =============================================================================

# --- 6. Edge cases ---

def test_spo2_dual_coding(g):
    spo2 = [o for o in typed(g, F.Observation) if str(o).endswith("-220277")]
    assert len(spo2) == 782
    for obs in spo2:
        assert {(LOINC, "2708-6"), (LOINC, "59408-5")} <= codings(g, one(g, obs, F["Observation.code"]))


def test_multi_interval_stays(g, src):
    per_stay = Counter(row["stay_id"] for row in src["careunit_intervals"])
    multi = {s: n for s, n in per_stay.items() if n > 1}
    assert multi, "expected at least one ICU stay with several care-unit intervals"
    for stay_id, n in multi.items():
        assert len(list(g.objects(DATA[f"icu-encounter-{stay_id}"], F["Encounter.location"]))) == n


def test_warning_flags(g, src):
    flagged = [r for r in src["observations"] if r["warning"] == "1"]
    true_flags = list(g.subjects(F["Extension.valueBoolean"], Literal(True)))
    assert len(flagged) == len(true_flags) == 1


def test_unmapped_admission_types_have_no_priority(g, src):
    unmapped = [r for r in src["hospital_admissions"]
                if r["admission_type"] in ("OBSERVATION ADMIT", "SURGICAL SAME DAY ADMISSION")]
    assert unmapped
    for row in unmapped:
        assert list(g.objects(DATA[f"hospital-encounter-{row['hadm_id']}"], F["Encounter.priority"])) == []


@pytest.mark.parametrize("raw, version, canonical", [
    ("41401", "9", "414.01"),
    ("V552", "9", "V55.2"),
    ("E8790", "9", "E879.0"),  # rule check only; no ICD-9 E-code occurs in this cohort
    ("4589", "9", "458.9"),
    ("E43", "10", "E43"),
    ("S0262XA", "10", "S02.62XA"),
    ("T814XXA", "10", "T81.4XXA"),
])
def test_canonical_icd_formatting(raw, version, canonical):
    """Check the ICD dot-insertion rule on known codes, including the ICD-9 E-code case that does not occur in the data."""
    assert gen.canonical_icd(raw, version) == canonical


def test_historical_icd_codes_not_modernized(g, src):
    for raw, canonical in [("S0262XA", "S02.62XA"), ("T814XXA", "T81.4XXA")]:
        rows = [r for r in src["first_ranked_diagnoses"] if r["icd_code"] == raw]
        assert len(rows) == 1
        actual = codings(g, one(g, DATA[f"condition-{rows[0]['hadm_id']}"], F["Condition.code"]))
        assert actual == {(EXPECTED_ICD_SYSTEMS["10"][0], raw), (EXPECTED_ICD_SYSTEMS["10"][1], canonical)}


def test_unapproved_source_values_fail():
    """Check that the generator raises ValueError on an unmapped admission type and on an already-dotted ICD code instead of passing them through."""
    with pytest.raises(ValueError):
        gen.lookup(gen.ADMISSION_PRIORITY, "UNSEEN TYPE", "admission_type")
    with pytest.raises(ValueError):
        gen.canonical_icd("414.01", "9")


# =============================================================================
# Scope: what must not be in the graph (the model §11 omissions, meta.profile,
# anything outside the fhir: vocabulary), plus the R4 plain-string form of uri values.
# =============================================================================

# --- Scope: deliberate omissions and no unsupported assertions ---

def test_scope(g):
    """Check selected scope constraints and the model's deliberate omissions.

    Only rdf:type and fhir: predicates are allowed. There must be no
    transfer_id or eventtype, neither as a predicate nor as an eventtype value
    ("admit", "transfer") under any predicate, and no meta.profile. This is not
    an exhaustive comparison of the graph against the model.
    """
    predicates = set(g.predicates())
    assert all(p == RDF.type or str(p).startswith(str(F)) for p in predicates)
    assert not any("transfer" in str(p).lower() or "eventtype" in str(p).lower() for p in predicates)
    assert F["Resource.meta"] not in predicates
    assert Literal("admit") not in set(g.objects()) and Literal("transfer") not in set(g.objects())


def test_uri_values_are_plain_strings(g):
    # R4 FHIR-RDF writes uri values untyped, so SPARQL can match them with a plain string.
    uri_predicates = ["Coding.system", "Identifier.system", "Quantity.system", "Extension.url"]
    for p in uri_predicates:
        values = list(g.objects(None, F[p]))
        assert values and all(isinstance(v, Literal) and v.datatype is None for v in values), p
    assert (None, F["Coding.system"], Literal(LOINC)) in g


# =============================================================================
# Reproducibility (handoff §6 criterion 8). Graphs with blank nodes cannot be
# compared line by line, so they are compared by their W3C RDFC-1.0 canonical
# form. rdflib.compare.isomorphic was tried first but had not finished after
# 7 minutes on this graph; RDFC-1.0 takes under a second.
# =============================================================================

# --- 7. Reproducibility ---

def canonical_form(path):
    """W3C RDFC-1.0 canonical N-Quads; equal canonical forms mean the graphs are isomorphic."""
    dataset = pyoxigraph.Dataset(pyoxigraph.Quad(t.subject, t.predicate, t.object)
                                 for t in pyoxigraph.parse(path=str(path), format=pyoxigraph.RdfFormat.TURTLE))
    dataset.canonicalize(pyoxigraph.CanonicalizationAlgorithm.RDFC_1_0)
    return sorted(pyoxigraph.serialize(dataset, format=pyoxigraph.RdfFormat.N_QUADS).decode().splitlines())


def test_committed_output_reproducible(tmp_path):
    """Check that the generator is deterministic and the committed file is up to date.

    Builds the graph twice, writes and re-parses each build as Turtle, and
    requires identical canonical forms for both builds and the committed file.
    A negative control changes one literal and requires the comparison to fail,
    proving the comparison can detect a difference.
    """
    fresh = []
    for name in ["a", "b"]:
        path = tmp_path / f"fresh_{name}.ttl"
        gen.build_graph(SOURCE).serialize(destination=path, format="turtle", encoding="utf-8")
        fresh.append(canonical_form(path))
    committed = canonical_form(TTL)
    assert fresh[0] == fresh[1]
    assert committed == fresh[0]

    # Negative control: changing a single literal must break canonical equality.
    mutated = tmp_path / "mutated.ttl"
    mutated.write_text((tmp_path / "fresh_a.ttl").read_text().replace('"10000032"', '"10000033"', 1))
    assert canonical_form(mutated) != committed
