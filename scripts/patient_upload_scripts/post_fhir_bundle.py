import json
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import os
import argparse

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://kis-lab.mi.intern/openmrs/ws/fhir2/R4"
AUTH = HTTPBasicAuth('superman', 'Admin123')
VERIFY_SSL = False

def update_references(data, id_mapping):
    """
    Recursively searches for 'reference' keys and replaces their values
    if they exist in the id_mapping dictionary.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k == 'reference' and isinstance(v, str):
                original_v = v
                updated = False
                
                # Wenn der genaue String im Mapping existiert, z.B. "urn:uuid:123..."
                if v in id_mapping:
                    data[k] = id_mapping[v]
                    updated = True
                # Manchmal ist die Reference nur die reine UUID, wir prüfen das auch
                elif v.replace('urn:uuid:', '') in id_mapping:
                    data[k] = id_mapping[v.replace('urn:uuid:', '')]
                    updated = True
                
                if updated:
                    print(f"    [!] Updated reference '{original_v}' -> '{data[k]}'")
                    
            elif isinstance(v, (dict, list)):
                update_references(v, id_mapping)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                update_references(item, id_mapping)

def post_fhir_entries(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            bundle = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return

    entries = bundle.get('entry', [])
    if not entries:
        print("No entries found in the bundle.")
        return

    print(f"Found {len(entries)} entries. Starting POST requests...\n")

    id_mapping = {}

    for index, entry in enumerate(entries, 1):
        resource = entry.get('resource')
        request_info = entry.get('request', {})
        full_url = entry.get('fullUrl')
        
        if not resource:
            print(f"[{index}/{len(entries)}] No resource found in entry, skipping.")
            continue
            
        # Wir entfernen die ursprüngliche ID, damit der Server gezwungen ist, 
        # eine neue zu generieren, falls er das nicht ohnehin tut.
        original_id = resource.pop('id', None)
        
        # Referenzen aktualisieren (z.B. subject.reference von Patient, partOf.reference von Encounter)
        update_references(resource, id_mapping)
        
        # Extrahiere relative URL
        relative_url = request_info.get('url', resource.get('resourceType'))
        
        url = f"{BASE_URL}/{relative_url}"
        resource_type = resource.get('resourceType', 'Unknown')
        
        print(f"[{index}/{len(entries)}] Posting {resource_type} to {url}...")
        
        try:
            response = requests.post(
                url,
                json=resource,
                auth=AUTH,
                verify=VERIFY_SSL,
                headers={"Content-Type": "application/fhir+json"}
            )
            
            if response.status_code in (200, 201):
                print(f"  -> Success! Status: {response.status_code}")
                
                new_id = None
                try:
                    resp_json = response.json()
                    new_id = resp_json.get('id')
                except ValueError:
                    pass
                
                # Fallback auf Location Header
                if not new_id and 'Location' in response.headers:
                    location = response.headers['Location']
                    parts = location.split('/')
                    # Location ist oft .../Patient/1234/_history/1
                    if len(parts) >= 3 and parts[-2] == '_history':
                        new_id = parts[-3]
                    elif len(parts) >= 2:
                        new_id = parts[-1]
                
                if new_id:
                    new_reference = f"{resource_type}/{new_id}"
                    
                    # Das Mapping wird mit verschiedenen Varianten gefüllt, 
                    # je nachdem, wie es im JSON referenziert wird.
                    if full_url:
                        id_mapping[full_url] = new_reference
                    if original_id:
                        id_mapping[original_id] = new_reference
                        id_mapping[f"urn:uuid:{original_id}"] = new_reference
                        
                    print(f"  -> Server ID: {new_id}")
                    print(f"  -> Mapped original IDs to: {new_reference}")
            else:
                print(f"  -> Failed. Status: {response.status_code}")
                # Wir geben nur die ersten 500 Zeichen aus, um nicht den Bildschirm mit HTML-Error-Pages zu fluten
                print(f"  -> Response: {response.text[:500]}")
                print(f"  -> Resource that failed: {json.dumps(resource, indent=2)}")
        except requests.exceptions.RequestException as e:
            print(f"  -> Error posting resource: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post FHIR bundle entries to a server.")
    parser.add_argument(
        "file_path", 
        nargs="?", 
        default=r"C:\Users\ronja\Bahmni\KIS-Projekt\Lukas92_Schmidt332_e5454f04-256d-0de3-0717-03556904d434 copy.json",
        help="Path to the FHIR JSON bundle file."
    )
    args = parser.parse_args()
    
    post_fhir_entries(args.file_path)
