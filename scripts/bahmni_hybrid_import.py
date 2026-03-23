import requests
import json
import urllib3
import os
import csv
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
INPUT_FILE = 'Lukas92_Schmidt332_e5454f04-256d-0de3-0717-03556904d434.json'
BASE_URL = 'https://localhost/openmrs'
AUTH = ('superman', 'Admin123')
CONCEPT_CSV = 'concept_mapping.csv' # Deine neue Lookup-Tabelle

# Endpunkte
URL_FHIR = f"{BASE_URL}/ws/fhir2/R4"
URL_REST = f"{BASE_URL}/ws/rest/v1"


ID_TYPE_NAME    = 'Patient Identifier'
# Standard-UUIDs (bitte an dein System anpassen)
ID_TYPE_UUID    = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
ENC_TYPE_UUID   = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
LOCATION_UUID   = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5' 
VISIT_TYPE_UUID = '54f43754-c6ce-4472-890e-0f28acaeaea6'
PROVIDER_UUID   = 'd7a67c17-5e07-11ef-8f7c-0242ac120002'
ROLE_UUID       = 'a0b03050-c99b-11e0-9572-0800200c9a66'

# --- KONZEPT-LOGIK (Lookups beschleunigen) ---
concept_cache = {}

def load_concept_cache():
    if os.path.exists(CONCEPT_CSV):
        with open(CONCEPT_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                concept_cache[row['code']] = row['uuid']
        print(f"✅ {len(concept_cache)} Konzepte aus CSV geladen.")

def get_concept_uuid(code):
    """Sucht erst in der CSV, dann via API."""
    if not code: return None
    if code in concept_cache: return concept_cache[code]
    
    # API Fallback (nur falls in CSV fehlt)
    try:
        r = requests.get(f"{URL_REST}/concept", params={'q': code}, auth=AUTH, verify=False)
        results = r.json().get('results', [])
        if results:
            new_uuid = results[0]['uuid']
            concept_cache[code] = new_uuid
            # In CSV anhängen für das nächste Mal
            with open(CONCEPT_CSV, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([code, new_uuid])
            return new_uuid
    except: pass
    return None

# --- HAUPTAPPLIKATION ---
def run_import():
    load_concept_cache()
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        bundle = json.load(f)

    # 1. Patientendaten extrahieren
    source_p = next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType'] == 'Patient')
    
    # Minimales, sauberes FHIR-Objekt für Bahmni bauen
    clean_patient = {
        "resourceType": "Patient",
        "active": True,
        "name": source_p.get('name'),
        "gender": source_p.get('gender'),
        "birthDate": source_p.get('birthDate'),
        "identifier": [
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            # Wir lassen das System weg, damit OpenMRS die UUID direkt matcht
                            "code": ID_TYPE_UUID,
                            "display": ID_TYPE_NAME
                        }
                    ],
                    "text": ID_TYPE_NAME
                },
                "value": source_p['identifier'][0]['value'],
                "extension": [
                    {
                        "url": "http://fhir.openmrs.org/ext/patient-identifier#preferred",
                        "valueBoolean": True
                    },
                    {
                        "url": "http://fhir.openmrs.org/ext/patient-identifier#location",
                        "valueReference": {
                            "reference": f"Location/{LOCATION_UUID}"
                        }
                    }
                ]
            }
        ]
    }

    print(f"[1] Lege Patient {clean_patient['name'][0]['family']} an (bereinigte Ressource)...")
    r_p = requests.post(f"{URL_FHIR}/Patient", json=clean_patient, auth=AUTH, verify=False)
    
    if r_p.status_code > 201:
        print(f"❌ Fehler Patient ({r_p.status_code}):")
        print(r_p.text)
        return
        
    patient_uuid = r_p.json()['id']
    print(f"✅ Patient angelegt: {patient_uuid}")

    # 2. Daten nach Encounter gruppieren
    encounters = {}
    observations = []
    
    for entry in bundle.get('entry', []):
        res = entry['resource']
        rtype = res['resourceType']
        if rtype == 'Encounter':
            encounters[entry['fullUrl']] = {
                'start': res['period']['start'],
                'end': res['period']['end'],
                'obs_list': []
            }
        elif rtype == 'Observation':
            observations.append(res)

    # 3. Observations ihren Encounters zuordnen
    for obs in observations:
        enc_ref = obs.get('encounter', {}).get('reference')
        if enc_ref in encounters:
            loinc = obs['code']['coding'][0].get('code')
            c_uuid = get_concept_uuid(loinc)
            
            if c_uuid:
                # Wert extrahieren (Zahl oder Text)
                val = obs.get('valueQuantity', {}).get('value') or obs.get('valueString')
                if val:
                    encounters[enc_ref]['obs_list'].append({"concept": c_uuid, "value": val})

    # 4. Visits und Encounter via REST anlegen
    print(f"\n[2] Verarbeite {len(encounters)} Besuche...")
    for urn, data in encounters.items():
        print(f"   -> Besuch am {data['start']} ({len(data['obs_list'])} Werte)")
        
        # A. Visit erstellen
        v_payload = {
            "patient": patient_uuid, "visitType": VISIT_TYPE_UUID, 
            "startDatetime": data['start'], "stopDatetime": data['end'], "location": LOCATION_UUID
        }
        r_v = requests.post(f"{URL_REST}/visit", json=v_payload, auth=AUTH, verify=False)
        if r_v.status_code > 201: continue
        
        # B. Encounter mit allen zugehörigen Observations in einem Rutsch
        e_payload = {
            "encounterDatetime": data['start'],
            "patient": patient_uuid, "encounterType": ENC_TYPE_UUID, 
            "location": LOCATION_UUID, "visit": r_v.json()['uuid'],
            "encounterProviders": [{"provider": PROVIDER_UUID, "encounterRole": ROLE_UUID}],
            "obs": data['obs_list']
        }
        requests.post(f"{URL_REST}/encounter", json=e_payload, auth=AUTH, verify=False)

    print("\n✅ Import abgeschlossen!")

if __name__ == "__main__":
    run_import()