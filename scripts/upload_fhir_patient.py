from codecs import encode
import requests
import json
import urllib3
# Konfiguration
BASE_URL = "https://localhost/openmrs/ws/fhir2/R4"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/fhir+json"}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def upload_sequentially(bundle_path):
    with open(bundle_path, 'r') as f:
        bundle = json.load(f)
    
    # Mapping von temporärer URN zur echten Server-ID
    id_map = {}
    for entry in bundle.get("entry", []):
        resource = entry["resource"]
        res_type = resource["resourceType"]
        temp_id = entry["fullUrl"]
        endpoint = entry["request"]["url"]

        # Referenzen aktualisieren, falls wir schon IDs aus vorherigen Schritten haben
        resource_str = json.dumps(resource, ensure_ascii=False)
        resource_str_debug = json.dumps(resource, indent=4)
        for old_id, new_id in id_map.items():
            resource_str = resource_str.replace(old_id, f"{res_type}/{new_id}")
            resource_str_debug = resource_str_debug.replace(old_id, f"{res_type}/{new_id}")
        # print(resource_str_debug)
        
        # Ressource an den spezifischen Endpunkt senden (z.B. /Patient)
        response = requests.post(
            f"{BASE_URL}/{endpoint}", 
            auth=AUTH, 
            headers=HEADERS, 
            data=resource_str,
            verify=False
        )

        if response.status_code in [200, 201]:
            new_id = response.json()["id"]
            id_map[temp_id] = new_id
            print(f"Erfolg: {res_type} erstellt mit ID {new_id}")
        else:
            print(f"Fehler bei {res_type} ({temp_id}): {response.status_code}")
            print(response.text)
# 22c20629-fb23-4510-ba40-fc96ced8cbe4
# Supersicherespasswort123!
# upload_sequentially("F:\Workspace\Bahmni_Project\Patienten JSON\Lukas92_Schmidt332_e5454f04-256d-0de3-0717-03556904d434_modified.json")
upload_sequentially(r"F:\Workspace\Bahmni_Project\Patienten JSON\Patient_02 copy.json")