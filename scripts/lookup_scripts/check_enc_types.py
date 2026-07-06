import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://localhost/openmrs/ws/rest/v1/encountertype'
auth = ('superman', 'Admin123')

try:
    response = requests.get(url, auth=auth, verify=False)
    data = response.json()
    
    print("--- Verfügbare Encounter Types ---")
    for entry in data.get('results', []):
        print(f"Name: {entry['display']}")
        print(f"UUID: {entry['uuid']}")
        print("-" * 30)
        
except Exception as e:
    print(f"Fehler: {e}")