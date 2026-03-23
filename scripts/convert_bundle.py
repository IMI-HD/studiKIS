import json
import uuid
import argparse
import requests
import urllib3
import tqdm 
import csv


# SSL Warnungen bei localhost unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
DEFAULT_INPUT = '0001310848.json'
DEFAULT_OUTPUT = 'bahmni_transaction_bundle.json'

# API Zugangsdaten für den Live-Lookup
DEFAULT_API_URL = 'https://localhost/openmrs/ws/rest/v1'
DEFAULT_USER = 'superman'
DEFAULT_PASS = 'Admin123'

# 1. PATIENT (Ihre ermittelte ID UUID)
DEFAULT_ID_UUID = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ID_NAME = 'Patient Identifier'

# 2. ENCOUNTER (Ihre ermittelte Encounter UUID)
# Bitte hier die UUID eintragen, die Sie zuletzt benutzt haben!
DEFAULT_ENC_UUID = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ENC_NAME = 'Consultation'

# 3. OBSERVATION (NEU: Hier UUID aus check_concepts.py eintragen)
# Platzhalter UUID - BITTE ERSETZEN!
DEFAULT_OBS_UUID = '160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
DEFAULT_OBS_NAME = 'Chief complaint (text)' 

# Fallback Diagnose (falls ICD-10 Code nicht gefunden wird)
DEFAULT_COND_UUID = 'd3686b3c-5e07-11ef-8f7c-0242ac120002' # Coded Diagnosis (bitte anpassen!)
DEFAULT_COND_NAME = 'Coded Diagnosis'

# 2. NEUE PFLICHTFELDER FÜR ENCOUNTER (Bitte anpassen!)
DEFAULT_LOC_UUID = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5' # z.B. für "OPD"
DEFAULT_LOC_NAME = 'OPD-1'

concept_cache = {}

def export_concepts_to_csv(api_url, auth, filename='concept_mapping.csv'):
    # Beispiel: Wir suchen nach häufigen Begriffen oder rufen eine Liste ab
    # Hinweis: Ein "Download ALL" ist über die REST-API oft langsam. 
    # Besser ist es, die CSV nach und nach beim ersten Lauf aufzubauen.
    print(f"Erstelle/Update lokale Mapping-Datei: {filename}")
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['code', 'uuid', 'display'])
        for code, (uuid, display) in concept_cache.items():
            writer.writerow([code, uuid, display])

def load_concept_cache_from_csv(filename='concept_mapping.csv'):
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                concept_cache[row['code']] = (row['uuid'], row['display'])
        print(f"{len(concept_cache)} Konzepte aus lokaler CSV geladen.")
    except FileNotFoundError:
        print("Keine lokale CSV gefunden. Starte mit leerem Cache.")

def get_concept_uuid_by_code(code, api_url, auth, fallback_uuid, csv_file='concept_mapping.csv'):
    if not code or code == '?': return fallback_uuid, "Unknown"
    
    # 1. Schneller lokaler Lookup
    if code in concept_cache: 
        return concept_cache[code]
    
    # 2. Nur wenn lokal nicht vorhanden: API-Call
    try:
        response = requests.get(f"{api_url}/concept", params={'q': code, 'v': 'custom:(uuid,display)'}, auth=auth, verify=False)
        results = response.json().get('results', [])
        if results:
            res_data = (results[0]['uuid'], results[0].get('display', code))
            concept_cache[code] = res_data
            
            # 3. Optional: Sofort in CSV speichern, damit es beim nächsten Mal da ist
            with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([code, res_data[0], res_data[1]])
                
            return res_data
    except: 
        pass
    
    return fallback_uuid, "Fallback Diagnosis"

def convert_to_transaction(args):
    try:
        with open(args.input, 'r', encoding='utf-8') as f: data = json.load(f)
    except: return

    auth = (args.user, args.password)
    transaction_bundle = { "resourceType": "Bundle", "type": "transaction", "entry": [] }
    id_map = {}

    for entry in data.get('entry', []):
        res = entry.get('resource')
        if res and res.get('id'):
            id_map[f"{res.get('resourceType')}/{res.get('id')}"] = f"urn:uuid:{uuid.uuid4()}"

    print(f"Konvertiere OHNE Provider (für Stabilität)...")

    for entry in tqdm.tqdm(data.get('entry', [])):
        res = entry.get('resource')
        if not res: continue
        rtype = res.get('resourceType')
        old_id = res.get('id')

        # --- 1. PATIENT: Namen aus Datei übernehmen ---
        if rtype == 'Patient':
            res['active'] = True
            # Falls Name in Datei vorhanden, diesen nutzen, sonst Default
            if 'name' in res and len(res['name']) > 0:
                pass # Wir lassen den Namen wie er ist
            else:
                res['name'] = [{"use": "official", "family": args.family, "given": [args.given]}]
            
            # Identifier für Bahmni/OpenMRS anpassen
            old_val = res.get('identifier', [{}])[0].get('value', 'Unknown')
            res['identifier'] = [{"use": "official", "type": { "coding": [{"code": args.id_uuid}], "text": args.id_name }, "value": old_val}]
            if 'address' in res: del res['address'] # Bahmni Adressfelder sind oft speziell

        # --- 2. ENCOUNTER: Stabilisierung ---
        elif rtype == 'Encounter':
            res['status'] = 'finished'
            res['class'] = { "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory" }
            res['location'] = [{"location": { "reference": f"Location/{args.loc_uuid}", "display": args.loc_name }}]
            if 'participant' in res: del res['participant']
            if 'serviceType' in res: del res['serviceType']

        # --- 3. OBSERVATION: LOINC-Mapping statt Hardcoded Code ---
        elif rtype == 'Observation':
            res['status'] = 'final'
            # Extrahiere LOINC Code aus der Synthea-Datei
            loinc_code = None
            try: loinc_code = res['code']['coding'][0].get('code')
            except: pass
            
            # Suche passendes OpenMRS Concept UUID für diesen LOINC Code
            real_uuid, real_name = get_concept_uuid_by_code(loinc_code, args.api_url, auth, args.obs_uuid)
            res['code'] = { "coding": [{"code": real_uuid, "display": real_name}], "text": real_name }
            
            if 'effectiveDateTime' not in res and 'issued' in res: 
                res['effectiveDateTime'] = res['issued']

        # --- 4. CONDITION / IMMUNIZATION / PROCEDURE: Dynamisches Mapping ---
        elif rtype in ['Condition', 'Immunization', 'Procedure']:
            target_code = None
            try:
                # SNOMED oder CVX Code extrahieren
                field = 'vaccineCode' if rtype == 'Immunization' else 'code'
                target_code = res[field]['coding'][0].get('code')
            except: pass
            
            # UUID aus OpenMRS suchen
            real_uuid, real_name = get_concept_uuid_by_code(target_code, args.api_url, auth, args.cond_uuid)
            
            field = 'vaccineCode' if rtype == 'Immunization' else 'code'
            res[field] = {"coding": [{"code": real_uuid, "display": real_name}], "text": real_name}

        # --- Bereinigung & Referenz-Fix ---
        if 'id' in res: del res['id']
        if 'meta' in res: del res['meta']
        
        # Referenzen innerhalb des Bundles aktualisieren (urn:uuid erhalten)
        res_str = json.dumps(res)
        for k, v in id_map.items(): res_str = res_str.replace(k, v)
        new_res = json.loads(res_str)
        
        full_url = id_map.get(f"{rtype}/{old_id}") or f"urn:uuid:{uuid.uuid4()}"
        transaction_bundle['entry'].append({
            "fullUrl": full_url, "resource": new_res, "request": {"method": "POST", "url": rtype}
        })

    with open(args.output, 'w', encoding='utf-8') as f: json.dump(transaction_bundle, f, indent=2)
    print("Fertig! Sauberes Bundle erstellt.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=DEFAULT_INPUT)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    parser.add_argument('--api-url', default=DEFAULT_API_URL)
    parser.add_argument('--user', default=DEFAULT_USER)
    parser.add_argument('--password', default=DEFAULT_PASS)
    parser.add_argument('--family', default="Mustermann")
    parser.add_argument('--given', default="Maria")
    parser.add_argument('--id-uuid', default=DEFAULT_ID_UUID)
    parser.add_argument('--id-name', default=DEFAULT_ID_NAME)
    parser.add_argument('--enc-uuid', default=DEFAULT_ENC_UUID)
    parser.add_argument('--enc-name', default=DEFAULT_ENC_NAME)
    parser.add_argument('--obs-uuid', default=DEFAULT_OBS_UUID)
    parser.add_argument('--obs-name', default=DEFAULT_OBS_NAME)
    parser.add_argument('--cond-uuid', default=DEFAULT_COND_UUID)
    parser.add_argument('--loc-uuid', default=DEFAULT_LOC_UUID)
    parser.add_argument('--loc-name', default=DEFAULT_LOC_NAME)
    
    # Provider wird ignoriert
    parser.add_argument('--prov-uuid', default="")
    parser.add_argument('--prov-name', default="")
    
    args = parser.parse_args()
    convert_to_transaction(args)