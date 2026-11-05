import requests
import json
import urllib3
import uuid  # Neu hinzugefügt für die Generierung von UUIDs

# SSL Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
SOURCE_NAME = "PACS Procedure Code"
VERIFY_SSL = False
SAME_AS_MAP_TYPE = "SAME-AS"

def get_resource(endpoint, params=None):
    response = requests.get(f"{BASE_URL}/{endpoint}", auth=AUTH, params=params, verify=VERIFY_SSL)
    return response.json() if response.status_code == 200 else None

def post_resource(endpoint, payload):
    response = requests.post(f"{BASE_URL}/{endpoint}", auth=AUTH, json=payload, headers=HEADERS, verify=VERIFY_SSL)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Fehler bei POST {endpoint}: {response.status_code} - {response.text}")
        return None

def setup_radiology_mapping(concept_display_name, concept_uuid=None):
    print(f"\n--- Verarbeite: {concept_display_name} ---")

    # 1. Sicherstellen, dass die Concept Source existiert
    source = get_resource("conceptsource", {"q": SOURCE_NAME})
    if not source or not source['results']:
        print(f"Erstelle Concept Source: {SOURCE_NAME}...")
        source = post_resource("conceptsource", {"name": SOURCE_NAME, "description": "Source for PACS Codes"})
        source_uuid = source['uuid']
    else:
        source_uuid = source['results'][0]['uuid']

    # 2. Konzept mit seinen Mappings abrufen
    # Direkt über die UUID: Die Namenssuche (q=...) liefert bei ähnlichen Namen
    # (z. B. "Echocardiogram" / "Transthoracic echocardiogram") sonst evtl. das falsche Konzept.
    rep = "custom:(uuid,display,mappings:(display))"
    if concept_uuid:
        concept_data = get_resource(f"concept/{concept_uuid}", {"v": rep})
    else:
        search = get_resource("concept", {"q": concept_display_name, "v": rep}) or {}
        concept_data = next((c for c in search.get("results", [])
                             if c.get("display", "").lower() == concept_display_name.lower()), None)
    if not concept_data:
        print(f"FEHLER: Konzept '{concept_display_name}' nicht gefunden.")
        return

    concept_uuid = concept_data['uuid']

    # Prüfen, ob bereits ein Mapping für diese Source existiert.
    # Die Anzeige eines Mappings lautet "<Source>: <Code>", z. B. "PACS Procedure Code: 2413aaa5-...".
    # (Früher wurde conceptSource am Reference Term geprüft - das ist in der REST-Antwort nicht enthalten,
    #  daher wurde ein vorhandenes Mapping nie erkannt.)
    if any((m.get('display') or '').startswith(f"{SOURCE_NAME}:") for m in concept_data.get('mappings', [])):
        print(f"Info: {concept_display_name} hat bereits ein PACS-Mapping. Überspringe...")
        return

    # 3. Neuen Reference Term erstellen (Code = UUID, Name = Konzeptname)
    new_pacs_code = str(uuid.uuid4()) # Generiert eine zufällige UUID
    print(f"Erstelle neuen Term: Name='{concept_display_name}', Code='{new_pacs_code}'")

    term_payload = {
        "code": new_pacs_code,
        "name": concept_display_name, # Hier wird der Name des Konzeptes gesetzt
        "conceptSource": source_uuid
    }

    new_term = post_resource("conceptreferenceterm", term_payload)
    if not new_term:
        return

    # 4. Nur das neue Mapping über die Sub-Resource hinzufügen
    #    (früher wurden alle Mappings neu gesendet -> Fehler "term.alreadyMapped")
    if post_resource(f"concept/{concept_uuid}/mapping", {
        "conceptReferenceTerm": new_term['uuid'],
        "conceptMapType": SAME_AS_MAP_TYPE
    }):
        print(f"ERFOLG: Mapping für {concept_display_name} mit UUID-Code erstellt.")

def get_radiology_orders():
    CONCEPT_NAME = "All Radiology orders"
    # 1. Suche nach dem Haupt-Konzept
    print(f"Suche nach Konzept: {CONCEPT_NAME}...")
    search_url = f"{BASE_URL}/concept"
    params = {'q': CONCEPT_NAME, 'v': 'full'} # 'full' ist wichtig für setMembers
    
    response = requests.get(search_url, auth=AUTH, params=params, verify=VERIFY_SSL)
    
    if response.status_code != 200:
        print(f"Fehler beim Abruf: {response.status_code}")
        return

    results = response.json().get('results', [])
    if not results:
        print("Kein Konzept mit diesem Namen gefunden.")
        return

    # Wir nehmen das erste Ergebnis
    concept_data = results[0]
    members = concept_data.get('setMembers', [])

    if not members:
        print(f"Das Konzept '{CONCEPT_NAME}' hat keine Mitglieder (setMembers).")
        return

    # Rekursiv: Unter-Sets (z. B. nach Fachgebiet gruppiert) bis zu den einzelnen Untersuchungen auflösen
    leaves = []
    def collect(member, depth=0):
        if depth > 5:
            return
        detail = get_resource(f"concept/{member['uuid']}", {"v": "custom:(uuid,display,set,setMembers:(uuid,display))"})
        if detail and detail.get('set'):
            for child in detail.get('setMembers', []):
                collect(child, depth + 1)
        else:
            leaves.append((member.get('display'), member['uuid']))
    for member in members:
        collect(member)
    return leaves


if __name__ == "__main__":
    # --- START ---
    # Da wir die Codes nun generieren, brauchen wir nur noch die Namen der Konzepte
    concepts_to_process = get_radiology_orders()

    for name, concept_uuid in concepts_to_process:
        # print(name)
        setup_radiology_mapping(name, concept_uuid)