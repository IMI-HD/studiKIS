import requests
import json
import urllib3
from datetime import datetime

# InsecureRequestWarning deaktivieren (lokale Testumgebung)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BAHMNI_BASE_URL = "https://localhost/openmrs"
URL_REST         = f"{BAHMNI_BASE_URL}/ws/rest/v1"
USERNAME         = "superman"
PASSWORD         = "Admin123"
AUTH             = (USERNAME, PASSWORD)
PATIENT_ID       = "ABC200001"

def get_rest(path, params=None):
    """Führt einen GET-Request gegen die OpenMRS REST API aus."""
    url = f"{URL_REST}/{path}"
    response = requests.get(url, params=params, auth=AUTH, verify=False)
    response.raise_for_status()
    return response.json()

def read_lab_values():
    print(f"--- Lese Laborwerte für Patient: {PATIENT_ID} ---")
    
    # 1. Patient suchen
    print(f"Suche Patient '{PATIENT_ID}'...")
    pat_search = get_rest("patient", {"q": PATIENT_ID, "v": "full"})
    results = pat_search.get("results", [])
    
    if not results:
        print(f"❌ Patient {PATIENT_ID} wurde nicht gefunden.")
        return
    
    patient = results[0]
    patient_uuid = patient["uuid"]
    print(f"✅ Patient gefunden: {patient['display']} (UUID: {patient_uuid})")
    
    # 2. Laborwerte (Observations) abrufen
    # In Bahmni werden Laborwerte oft in Observations gespeichert.
    # Wir suchen nach Observations für diesen Patienten.
    print(f"Rufe Labor-Observations ab...")
    obs_data = get_rest("obs", {
        "patient": patient_uuid,
        "v": "custom:(display,value,obsDatetime,concept:(display,name))",
        "limit": 50
    })
    
    observations = obs_data.get("results", [])
    
    if not observations:
        print("ℹ️ Keine Laborwerte (Observations) für diesen Patienten gefunden.")
        return

    print("\n--- Gefundene Werte ---")
    print(f"{'Datum':<20} | {'Test':<30} | {'Wert':<10}")
    print("-" * 65)
    
    found_any = False
    for obs in observations:
        display = obs.get("display", "")
        # Filtere nach typischen Laborkonzepten oder schlage alle Observations vor
        # Da wir ein minimales Skript wollen, geben wir einfach alle Observations aus
        # und weisen darauf hin, dass dies die 'Lab Results' sind.
        
        # DEBUG: Full JSON
        print(f"DEBUG: {json.dumps(obs, indent=2)}")
        
        date_val = obs.get("obsDatetime") or ""
        date_str = str(date_val)[:16].replace("T", " ")
        
        concept = obs.get("concept") or {}
        concept_name = str(concept.get("display") or "Unbekannt")
        
        value = str(obs.get("value") or "")
        
        # In Bahmni sind Lab-Observations oft Teil eines "Lab Set"
        print(f"{date_str:<20} | {concept_name:<30} | {value:<10}")
        found_any = True
        
    if not found_any:
        print("Keine spezifischen Laborwerte gefunden.")

if __name__ == "__main__":
    try:
        read_lab_values()
    except Exception as e:
        print(f"❌ Fehler: {e}")
