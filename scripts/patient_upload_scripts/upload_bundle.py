import json
import requests
import sys

# --- KONFIGURATION ---
BUNDLE_FILE = 'bahmni_transaction_bundle.json'
BASE_URL = 'https://localhost/openmrs/ws/fhir2/R4' # Achten Sie auf http vs https
AUTH = ('superman', 'Admin123')
VERIFY_SSL = False  # Bei localhost oft notwendig

def upload_bundle():
    print(f"Lade {BUNDLE_FILE}...")
    try:
        with open(BUNDLE_FILE, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")
        return

    # Versuch 1: Als Transaction senden (Der "saubere" Weg)
    print("\n--- Versuch 1: Transaction Import ---")
    headers = {'Content-Type': 'application/fhir+json'}
    
    try:
        response = requests.post(BASE_URL, json=bundle, headers=headers, auth=AUTH, verify=VERIFY_SSL)
        
        if response.status_code in [200, 201]:
            print("ERFOLG! Das Bundle wurde als Transaktion verarbeitet.")
            print(response.json())
            return
        else:
            print(f"Transaction fehlgeschlagen. Status: {response.status_code}")
            print(f"Server Antwort: {response.text[:200]}...")
            print(">> Wechsel zu Plan B (Einzel-Upload)...")

    except Exception as e:
        print(f"Verbindungsfehler: {e}")
        print(">> Wechsel zu Plan B (Einzel-Upload)...")

    # Versuch 2: Client-Side Resolution (Wenn der Server keine Transactions kann)
    print("\n--- Versuch 2: Smart Einzel-Upload ---")
    
    # 1. Suche den Patienten im Bundle
    patient_entry = next((e for e in bundle['entry'] if e['resource']['resourceType'] == 'Patient'), None)
    if not patient_entry:
        print("Kein Patient im Bundle gefunden! Abbruch.")
        return

    # Mapping Tabelle für IDs (Temp ID -> Echte Server ID)
    id_map = {}
    temp_patient_id = patient_entry['fullUrl'] # z.B. urn:uuid:2a8e...

    # 2. Patient hochladen
    print(f"Lade Patient hoch ({temp_patient_id})...")
    p_res = requests.post(f"{BASE_URL}/Patient", json=patient_entry['resource'], headers=headers, auth=AUTH, verify=VERIFY_SSL)
    
    if p_res.status_code not in [200, 201]:
        print(f"Fehler beim Erstellen des Patienten: {p_res.text}")
        return
    
    real_patient_id = p_res.json()['id']
    id_map[temp_patient_id] = f"Patient/{real_patient_id}"
    print(f"Patient erstellt! Echte ID: {real_patient_id}")

    # 3. Restliche Ressourcen hochladen und Referenzen fixen
    for entry in bundle['entry']:
        resource = entry['resource']
        rtype = resource['resourceType']
        
        if rtype == 'Patient': 
            continue # Schon erledigt

        # Referenzen im JSON String ersetzen (Subject: urn:uuid... -> Patient/123)
        res_str = json.dumps(resource)
        for temp_id, real_id in id_map.items():
            res_str = res_str.replace(temp_id, real_id)
        
        updated_resource = json.loads(res_str)

        # Hochladen
        print(f"Lade {rtype} hoch...")
        print(updated_resource)
        stop
        res = requests.post(f"{BASE_URL}/{rtype}", json=updated_resource, headers=headers, auth=AUTH, verify=VERIFY_SSL)
        
        if res.status_code in [200, 201]:
            # Falls wir diese Ressource später referenzieren müssten (z.B. Encounter für Condition), ID speichern
            if 'fullUrl' in entry:
                new_id = res.json()['id']
                id_map[entry['fullUrl']] = f"{rtype}/{new_id}"
            print(f"  -> OK ({rtype})")
        else:
            print(f"  -> FEHLER bei {rtype}: {res.status_code} - {res.text}")
            stop

if __name__ == "__main__":
    # Unterdrücke SSL Warnungen für saubereren Output
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    upload_bundle()