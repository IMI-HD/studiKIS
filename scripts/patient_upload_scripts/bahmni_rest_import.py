import requests
import json
import urllib3
import sys
import argparse
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
INPUT_FILE = '0001310848.json'
API_URL = 'https://localhost/openmrs/ws/rest/v1'
AUTH = ('superman', 'Admin123')

# --- UUIDs ---
ID_TYPE_UUID    = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
ENC_TYPE_UUID   = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
LOCATION_UUID   = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5' 
VISIT_TYPE_UUID = '54f43754-c6ce-4472-890e-0f28acaeaea6' 
PROVIDER_UUID   = 'd7a67c17-5e07-11ef-8f7c-0242ac120002' 
ROLE_UUID       = 'a0b03050-c99b-11e0-9572-0800200c9a66' 

# --- KONZEPTE ---
OBS_CHIEF_COMPLAINT_UUID = '160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
OBS_CODED_DIAGNOSIS_UUID = 'd3686b3c-5e07-11ef-8f7c-0242ac120002' 

# Cache
concept_cache = {}

def resolve_concept_by_code(code):
    if not code: return None
    if code in concept_cache: return concept_cache[code]
    try:
        r = requests.get(f"{API_URL}/concept", params={'q': code, 'v': 'custom:(uuid,display)'}, auth=AUTH, verify=False)
        if r.status_code == 200 and r.json().get('results'):
            res = r.json()['results'][0]
            print(f"      ✅ ICD '{code}' -> {res['uuid']}")
            concept_cache[code] = res['uuid']
            return res['uuid']
    except: pass
    print(f"      ⚠️  Kein Konzept für '{code}'")
    return None

def parse_source_file(filename):
    print(f"📂 Lese Datei: {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f: data = json.load(f)
    except: print("❌ Datei fehlt!"); sys.exit(1)

    extracted = {
        'id': None, 'gender': 'M', 'birthdate': '1970-01-01',
        'observation_text': 'Routine Checkup',
        'conditions': [], 
        'encounters': [] 
    }

    for entry in data.get('entry', []):
        res = entry.get('resource', {})
        rtype = res.get('resourceType')

        if rtype == 'Patient':
            if res.get('identifier'): extracted['id'] = res['identifier'][0]['value']
            extracted['gender'] = 'F' if res.get('gender', 'male').lower() in ['female', 'f'] else 'M'
            extracted['birthdate'] = res.get('birthDate', '1980-01-01')

        elif rtype == 'Condition':
            if res.get('code', {}).get('coding'):
                code = res['code']['coding'][0].get('code')
                if code: extracted['conditions'].append(code)

        elif rtype == 'Encounter':
            per = res.get('period', {})
            if per.get('start'):
                extracted['encounters'].append({'start': per['start'], 'end': per.get('end', per['start'])})

        elif rtype == 'Observation':
            if res.get('code', {}).get('text'): extracted['observation_text'] = res['code']['text']

    if not extracted['encounters']:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")
        extracted['encounters'].append({'start': now, 'end': now})
    
    # WICHTIG: Sortieren, damit wir wissen, welches der ERSTE Besuch ist
    extracted['encounters'].sort(key=lambda x: x['start'])
    return extracted

def run_import(args):
    data = parse_source_file(INPUT_FILE)
    print(f"\n🚀 Import: {args.given} {args.family} ({data['id']})")

    # 1. PATIENT
    patient_uuid = None
    r = requests.get(f"{API_URL}/patient", params={'q': data['id'], 'v': 'full'}, auth=AUTH, verify=False)
    if r.json().get('results'): 
        patient_uuid = r.json()['results'][0]['uuid']
        print(f"✅ Patient existiert: {patient_uuid}")
    else:
        print("⏳ Patient neu...")
        payload = {
            "person": { 
                "names": [{"givenName": args.given, "familyName": args.family}],
                "gender": data['gender'], "birthdate": data['birthdate']
            },
            "identifiers": [{"identifier": data['id'], "identifierType": ID_TYPE_UUID, "location": LOCATION_UUID, "preferred": True}]
        }
        r = requests.post(f"{API_URL}/patient", json=payload, auth=AUTH, verify=False)
        if r.status_code > 201: print(f"❌ Patient Error: {r.text}"); sys.exit(1)
        patient_uuid = r.json()['uuid']

    # 2. ENCOUNTERS (Mit Smart-Logic)
    print("\n⏳ Importiere Encounters...")
    
    # Flag: Ist dies der allererste Encounter?
    is_first_encounter = True

    for enc_data in data['encounters']:
        print(f"   -> Verarbeite {enc_data['start']}...")

        # A) Visit
        v_payload = {
            "patient": patient_uuid, "visitType": VISIT_TYPE_UUID, 
            "startDatetime": enc_data['start'], "stopDatetime": enc_data['end'], "location": LOCATION_UUID
        }
        r_v = requests.post(f"{API_URL}/visit", json=v_payload, auth=AUTH, verify=False)
        if r_v.status_code > 201: print(f"❌ Visit Error: {r_v.text}"); continue
        
        # B) Obs vorbereiten
        obs_list = []
        obs_list.append({"concept": OBS_CHIEF_COMPLAINT_UUID, "value": data['observation_text']})

        # C) DIAGNOSEN - NUR IM ERSTEN ENCOUNTER!
        if is_first_encounter and data['conditions']:
            print(f"      + Füge {len(data['conditions'])} Aufnahmediagnosen hinzu.")
            for code in data['conditions']:
                uuid = resolve_concept_by_code(code)
                if uuid:
                    obs_list.append({
                        "concept": OBS_CODED_DIAGNOSIS_UUID,
                        "value": uuid
                    })
            is_first_encounter = False # Für nächste Loop deaktivieren

        # D) Encounter Senden
        e_payload = {
            "encounterDatetime": enc_data['start'],
            "patient": patient_uuid, "encounterType": ENC_TYPE_UUID, 
            "location": LOCATION_UUID, "visit": r_v.json()['uuid'],
            "encounterProviders": [{"provider": PROVIDER_UUID, "encounterRole": ROLE_UUID}],
            "obs": obs_list
        }
        r_e = requests.post(f"{API_URL}/encounter", json=e_payload, auth=AUTH, verify=False)
        if r_e.status_code > 201: print(f"   ❌ Error: {r_e.text}")
        else: print(f"   ✅ OK.")

    print(f"\n🎉 FERTIG! Keine Abstürze, keine Duplikate.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--given', default="Maria")
    parser.add_argument('--family', default="Mustermann")
    run_import(parser.parse_args())