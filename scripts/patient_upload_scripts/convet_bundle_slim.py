import json
import uuid
import argparse

# --- IHRE KONFIGURATION ---
DEFAULT_INPUT = '0001310848.json'
DEFAULT_OUTPUT = 'bahmni_phase2_encounter_visit.json'

DEFAULT_ID_UUID = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ID_NAME = 'Patient Identifier'

# Encounter (Consultation)
DEFAULT_ENC_UUID = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ENC_NAME = 'Consultation'

# Location (OPD-1)
DEFAULT_LOC_UUID = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5'
DEFAULT_LOC_NAME = 'OPD-1'

def convert_to_transaction(args):
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Fehler: Datei '{args.input}' nicht gefunden.")
        return

    transaction_bundle = {
        "resourceType": "Bundle", "type": "transaction", "entry": []
    }
    id_map = {}

    # UUIDs vor-generieren
    for entry in data.get('entry', []):
        res = entry.get('resource')
        if res and res.get('id'):
            id_map[f"{res.get('resourceType')}/{res.get('id')}"] = f"urn:uuid:{uuid.uuid4()}"

    print("Erstelle Phase 2 Fix: Encounter als 'VISIT' markieren...")

    for entry in data.get('entry', []):
        res = entry.get('resource')
        if not res: continue
        rtype = res.get('resourceType')
        old_id = res.get('id')

        if rtype == 'Patient':
            res['name'] = [{"use": "official", "family": args.family, "given": [args.given]}]
            res['active'] = True
            old_val = res.get('identifier', [{}])[0].get('value', 'Unknown')
            res['identifier'] = [{
                "use": "official",
                "type": { "coding": [{"code": DEFAULT_ID_UUID}], "text": DEFAULT_ID_NAME },
                "value": old_val
            }]
            if 'address' in res: del res['address']

        elif rtype == 'Encounter':
            res['status'] = 'finished'
            
            # --- WICHTIG: TAG ALS VISIT ---
            # Ohne diesen Tag weiß das Dashboard nicht, dass dies ein Besuch ist -> Crash.
            res['meta'] = {
                "tag": [
                    {
                        "system": "http://fhir.openmrs.org/ext/encounter-tag",
                        "code": "visit",
                        "display": "Visit"
                    }
                ]
            }

            res['type'] = [{
                "coding": [{
                    "system": "http://fhir.openmrs.org/code-system/encounter-type",
                    "code": DEFAULT_ENC_UUID,
                    "display": DEFAULT_ENC_NAME
                }],
                "text": DEFAULT_ENC_NAME
            }]
            
            # Class AMB
            res['class'] = { 
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", 
                "code": "AMB", 
                "display": "ambulatory" 
            }
            if 'serviceType' in res: del res['serviceType']
            
            res['location'] = [{
                "location": {
                    "reference": f"Location/{DEFAULT_LOC_UUID}",
                    "display": DEFAULT_LOC_NAME
                }
            }]

            # Provider weiterhin weglassen für Test
            if 'participant' in res: del res['participant']

        else:
            continue # Obs/Conditions ignorieren

        # Cleanup (meta aber behalten, da wir es gerade gesetzt haben!)
        if 'id' in res: del res['id']
        # if 'meta' in res: del res['meta']  <-- Das darf NICHT gelöscht werden, sonst ist der Tag weg!
        
        # Nur versions-spezifische Meta-Daten löschen, falls nötig
        if 'meta' in res and 'versionId' in res['meta']: del res['meta']['versionId']
        if 'meta' in res and 'lastUpdated' in res['meta']: del res['meta']['lastUpdated']
        
        res_str = json.dumps(res)
        for k, v in id_map.items(): res_str = res_str.replace(k, v)
        new_res = json.loads(res_str)
        full_url = id_map.get(f"{rtype}/{old_id}") or f"urn:uuid:{uuid.uuid4()}"
        
        transaction_bundle['entry'].append({
            "fullUrl": full_url,
            "resource": new_res,
            "request": {"method": "POST", "url": rtype}
        })

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(transaction_bundle, f, indent=2)
    print(f"Fertig! Datei '{args.output}' erstellt.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=DEFAULT_INPUT)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    parser.add_argument('--family', default="Mustermann")
    parser.add_argument('--given', default="Maria")
    
    args = parser.parse_args()
    convert_to_transaction(args)