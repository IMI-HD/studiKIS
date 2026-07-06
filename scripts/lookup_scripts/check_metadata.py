import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = ('superman', 'Admin123')
base_url = 'https://localhost/openmrs/ws/rest/v1'

def get_first(endpoint, name):
    try:
        r = requests.get(f"{base_url}/{endpoint}", auth=auth, verify=False)
        results = r.json().get('results', [])
        if results:
            print(f"--- {name} ---")
            print(f"Name: {results[0]['display']}")
            print(f"UUID: {results[0]['uuid']}")
    except Exception as e:
        print(f"Fehler bei {name}: {e}")

get_first('location?q=OPD', 'Location (Empfehlung: OPD)')
get_first('provider?q=superman', 'Provider (Empfehlung: Superman)')