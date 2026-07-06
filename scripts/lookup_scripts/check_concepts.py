import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suchen wir nach Konzepten, die oft da sind
SEARCH_TERMS = ["Chief Complaint", "History", "Diagnosis", "Weight", "Height"]

url_base = 'https://localhost/openmrs/ws/rest/v1/concept?q='
auth = ('superman', 'Admin123')

print("--- Suche nach Konzepten ---")
for term in SEARCH_TERMS:
    try:
        response = requests.get(url_base + term, auth=auth, verify=False)
        results = response.json().get('results', [])
        
        for entry in results:
            print(f"Name: {entry['display']}")
            print(f"UUID: {entry['uuid']}")
            # Wir nehmen nur den ersten Treffer pro Begriff, damit die Liste kurz bleibt
            break 
    except Exception as e:
        print(f"Fehler bei '{term}': {e}")

print("-" * 30)