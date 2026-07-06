import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = ('superman', 'Admin123')
url = 'https://localhost/openmrs/ws/rest/v1'

print("--- UUID ANALYSE ---")

# 1. Provider suchen (DAS BRAUCHEN WIR!)
try:
    r = requests.get(f"{url}/provider?q=superman", auth=auth, verify=False)
    results = r.json()['results']
    if results:
        print(f"✅ PROVIDER UUID: {results[0]['uuid']}  <-- DIESE UUID KOPIEREN!")
        print(f"✅ PROVIDER UUID: {results[0]}  <-- DIESE UUID KOPIEREN!")
    else:
        print("❌ Kein Provider 'superman' gefunden.")
except Exception as e:
    print(f"Fehler bei Provider-Suche: {e}")

# 2. User suchen (DAS HABEN SIE VERMUTLICH GENUTZT)
try:
    r = requests.get(f"{url}/user?q=superman", auth=auth, verify=False)
    results = r.json()['results']
    if results:
        print(f"⚠️  USER UUID:     {results[0]['uuid']}  <-- NICHT VERWENDEN!")
except: pass