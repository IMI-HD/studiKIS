import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = ('superman', 'Admin123')
url = 'https://localhost/openmrs/ws/rest/v1/encounterrole'

print("--- Verfügbare Encounter Roles ---")
try:
    r = requests.get(url, auth=auth, verify=False)
    results = r.json().get('results', [])
    for entry in results:
        print(f"Name: {entry['display']}")
        print(f"UUID: {entry['uuid']}")
        print("-" * 20)
except Exception as e:
    print(f"Fehler: {e}")