"""
openmrs_report.py - store radiology findings as text observations in Bahmni/OpenMRS.

The finding is saved with the concept "Radiology Finding" and shows up in the
clinical dashboard section "radiologyFinding"
(standard-config/openmrs/apps/clinical/dashboard.json).

The obs is deliberately NOT linked to the order via obs.order: Bahmni's dashboard
query (bahmnicore/observations) hides order-linked obs by default, and the orders
control did not return them on our instance either. Instead the order number is
stored in the obs comment ("Order ORD-123"), which is also shown in the dashboard
and used to detect duplicates.

Usage from pacs_injector.py:
    from openmrs_report import publish_report_for_order
    publish_report_for_order(patient_uuid, order_uuid, report_text)

CLI:
    python openmrs_report.py check                                  # verify configuration
    python openmrs_report.py setup                                  # create concept + encounter type if missing, then check
    python openmrs_report.py test <patient> <order_number> [text]   # write a test finding
        <patient> may be the patient UUID or the patient identifier (e.g. GAN203006)
    python openmrs_report.py void <encounter_uuid>                  # void (soft-delete) an encounter
"""

import re
import sys
import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --------------------------------------------------------------------------
# Configuration - adjust to your Bahmni instance
# --------------------------------------------------------------------------
OPENMRS_REST_URL = "https://localhost/openmrs/ws/rest/v1"
OPENMRS_AUTH = ("superman", "Admin123")
VERIFY_SSL = False                      # Bahmni Docker uses a self-signed certificate

REPORT_CONCEPT_NAME = "Radiology Finding"   # default concept (dashboard section "radiologyFinding")
ECG_CONCEPT_NAME = "ECG Finding"            # ECGs are ordered as radiology orders but shown separately
REPORT_CONCEPTS = [REPORT_CONCEPT_NAME, ECG_CONCEPT_NAME]   # created by "setup", verified by "check"
# Must NOT be "RADIOLOGY": the dashboard section "radiology" (documents control) loads all
# RADIOLOGY encounters and expects every obs to be a document obs group -> UI crash.
ENCOUNTER_TYPE_NAME = "Radiology Report"
LOCATION_NAME = "Kardiologie"           # fallback location if the order's ward is unknown
VISIT_TYPE = "OPD"                      # must be an existing visit type
SET_FULFILLER_STATUS = True             # mark order as COMPLETED (OpenMRS >= 2.2)

UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

session = requests.Session()
session.auth = OPENMRS_AUTH
session.verify = VERIFY_SSL
session.headers.update({"Content-Type": "application/json"})

_cache = {}


def log(msg):
    print(f"[openmrs_report] {msg}")


# --------------------------------------------------------------------------
# Lookups
# --------------------------------------------------------------------------
def _get(path, **params):
    r = session.get(f"{OPENMRS_REST_URL}/{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def lookup_uuid(resource, name):
    """Return the UUID of a resource with exactly this name (case-insensitive, cached)."""
    key = (resource, name.lower())
    if key in _cache:
        return _cache[key]
    results = _get(resource, q=name).get("results", [])
    match = next((x for x in results if x.get("display", "").lower() == name.lower()), None)
    if match is None:
        found = ", ".join(x.get("display", "?") for x in results[:5]) or "-"
        raise LookupError(f"{resource} '{name}' not found (similar: {found})")
    _cache[key] = match["uuid"]
    return match["uuid"]


def resolve_patient_uuid(patient):
    """Accept a patient UUID or a patient identifier and return the UUID."""
    if UUID_PATTERN.match(patient):
        return patient
    results = _get("patient", identifier=patient, v="custom:(uuid)").get("results", [])
    if not results:
        raise LookupError(f"patient '{patient}' not found")
    return results[0]["uuid"]


def find_order(patient_uuid, order_number):
    """Find a patient's order by order number or accession number (active orders only)."""
    orders = _get("order", patient=patient_uuid,
                  v="custom:(uuid,orderNumber,accessionNumber,concept:(display))").get("results", [])
    for o in orders:
        if order_number in (o.get("orderNumber"), o.get("accessionNumber")):
            return o
    raise LookupError(f"order {order_number} for patient {patient_uuid} not found (or no longer active)")


def order_comment(order_number):
    return f"Order {order_number}"


def get_order_number(order_uuid):
    return _get(f"order/{order_uuid}", v="custom:(orderNumber)")["orderNumber"]


def report_exists(patient_uuid, order_number, concept_name=REPORT_CONCEPT_NAME):
    """Prevent duplicate findings if a trigger is processed twice (matched via obs comment)."""
    concept_uuid = lookup_uuid("concept", concept_name)
    obs = _get("obs", patient=patient_uuid, concept=concept_uuid,
               v="custom:(uuid,comment)").get("results", [])
    return any(o.get("comment") == order_comment(order_number) for o in obs)


# --------------------------------------------------------------------------
# Write finding
# --------------------------------------------------------------------------
def resolve_location_uuid(location_name):
    """Use the given location (e.g. the order's ward); fall back to LOCATION_NAME if it is unknown."""
    if location_name:
        try:
            return lookup_uuid("location", location_name)
        except LookupError:
            log(f"location '{location_name}' not found - using '{LOCATION_NAME}'")
    return lookup_uuid("location", LOCATION_NAME)


def post_report(patient_uuid, order_number, report_text,
                concept_name=REPORT_CONCEPT_NAME, location_name=None):
    payload = {
        "patientUuid": patient_uuid,
        "visitType": VISIT_TYPE,
        "encounterTypeUuid": lookup_uuid("encountertype", ENCOUNTER_TYPE_NAME),
        "locationUuid": resolve_location_uuid(location_name),
        "observations": [{
            "concept": {"uuid": lookup_uuid("concept", concept_name),
                        "name": concept_name},
            "value": report_text,
            "comment": order_comment(order_number),
        }],
    }
    r = session.post(f"{OPENMRS_REST_URL}/bahmnicore/bahmniencounter", json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"bahmniencounter failed ({r.status_code}): {r.text[:500]}")
    return r.json()


def mark_order_completed(order_uuid):
    r = session.post(f"{OPENMRS_REST_URL}/order/{order_uuid}/fulfillerdetails",
                     json={"fulfillerStatus": "COMPLETED",
                           "fulfillerComment": "Radiology finding available"}, timeout=15)
    if not r.ok:
        log(f"note: fulfiller status not set ({r.status_code}) - finding was saved anyway")


def publish_report_for_order(patient_uuid, order_uuid, report_text,
                             concept_name=REPORT_CONCEPT_NAME, location_name=None):
    """
    Main entry point for pacs_injector.py (patient and order UUID already known).
    concept_name: REPORT_CONCEPT_NAME (default) or e.g. ECG_CONCEPT_NAME.
    location_name: location of the finding (e.g. the order's ward); falls back to LOCATION_NAME.
    Returns the encounter UUID, or None if a finding for this order already exists.
    """
    order_number = get_order_number(order_uuid)
    if report_exists(patient_uuid, order_number, concept_name):
        log(f"finding for order {order_number} already exists - skipped")
        return None
    result = post_report(patient_uuid, order_number, report_text, concept_name, location_name)
    if SET_FULFILLER_STATUS:
        mark_order_completed(order_uuid)
    enc = result.get("encounterUuid")
    log(f"{concept_name} for order {order_number} saved in OpenMRS (encounter {enc})")
    return enc


def publish_report(patient, order_number, report_text=None):
    """Variant with patient UUID/identifier and order number (used by the CLI test)."""
    patient_uuid = resolve_patient_uuid(patient)
    order = find_order(patient_uuid, order_number)
    if report_text is None:
        label = (order.get("concept") or {}).get("display", "Radiology")
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        report_text = (f"Examination: {label}\nDate: {now}\n\n"
                       "Findings: Test finding written by openmrs_report.py.\n\n"
                       "Impression: Test only.")
    return publish_report_for_order(patient_uuid, order["uuid"], report_text)


# --------------------------------------------------------------------------
# Setup / check
# --------------------------------------------------------------------------
def setup_concept(concept_name):
    """Create a text concept if it does not exist yet."""
    try:
        uuid = lookup_uuid("concept", concept_name)
        print(f"Concept already exists: {concept_name} {uuid}")
        return uuid
    except LookupError:
        pass
    payload = {
        "names": [{"name": concept_name, "locale": "en",
                   "localePreferred": True, "conceptNameType": "FULLY_SPECIFIED"}],
        "datatype": lookup_uuid("conceptdatatype", "Text"),
        "conceptClass": lookup_uuid("conceptclass", "Finding"),
    }
    r = session.post(f"{OPENMRS_REST_URL}/concept", json=payload, timeout=15)
    r.raise_for_status()
    print(f"Concept created: {concept_name} {r.json()['uuid']}")
    return r.json()["uuid"]


def setup_encounter_type():
    """Create the encounter type for findings if it does not exist yet."""
    try:
        uuid = lookup_uuid("encountertype", ENCOUNTER_TYPE_NAME)
        print(f"Encounter type already exists: {uuid}")
        return uuid
    except LookupError:
        pass
    r = session.post(f"{OPENMRS_REST_URL}/encountertype",
                     json={"name": ENCOUNTER_TYPE_NAME,
                           "description": "Radiology finding (text) linked to a radiology order"},
                     timeout=15)
    r.raise_for_status()
    print(f"Encounter type created: {r.json()['uuid']}")
    return r.json()["uuid"]


def void_encounter(encounter_uuid):
    """Void (soft-delete) an encounter including its observations."""
    r = session.delete(f"{OPENMRS_REST_URL}/encounter/{encounter_uuid}",
                       params={"reason": "removed by openmrs_report.py"}, timeout=15)
    if not r.ok:
        raise RuntimeError(f"void failed ({r.status_code}): {r.text[:500]}")
    print(f"Encounter voided: {encounter_uuid}")


def check_config():
    ok = True
    for resource, name in [*(("concept", c) for c in REPORT_CONCEPTS),
                           ("encountertype", ENCOUNTER_TYPE_NAME),
                           ("location", LOCATION_NAME),
                           ("visittype", VISIT_TYPE)]:
        try:
            print(f"OK      {resource:14} {name:20} {lookup_uuid(resource, name)}")
        except Exception as e:
            ok = False
            print(f"MISSING {resource:14} {name:20} ({e})")
    for concept_name in REPORT_CONCEPTS:
        try:
            c = _get(f"concept/{lookup_uuid('concept', concept_name)}",
                     v="custom:(datatype:(display))")
            dtype = (c.get("datatype") or {}).get("display")
            if dtype != "Text":
                ok = False
                print(f"WARNING concept '{concept_name}' datatype is '{dtype}', expected 'Text'")
        except LookupError:
            pass
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        sys.exit(0 if check_config() else 1)
    elif cmd == "setup":
        for concept_name in REPORT_CONCEPTS:
            setup_concept(concept_name)
        setup_encounter_type()
        sys.exit(0 if check_config() else 1)
    elif cmd == "test" and len(sys.argv) >= 4:
        text = sys.argv[4] if len(sys.argv) >= 5 else None
        publish_report(sys.argv[2], sys.argv[3], text)
    elif cmd == "void" and len(sys.argv) >= 3:
        void_encounter(sys.argv[2])
    else:
        print(__doc__)
