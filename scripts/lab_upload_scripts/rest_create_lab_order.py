import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time
import json

# Credentials and Settings
BASE_URL = "https://localhost/openmrs/ws/rest/v1"
CREATE_LAB_ORDER_END_POINT = f"{BASE_URL}/bahmnicore/bahmniencounter"
AUTH = HTTPBasicAuth('superman', 'Admin123')
VERIFY_SSL = False

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_provider_data(PROVIDER_NAME, ENCOUNTER_ROLE_NAME):
    PROVIDER_UUID = None
    ENCOUNTER_ROLE_UUID = None

    try:
        # Get Provider UUID
        provider_response = requests.get(
            f"{BASE_URL}/provider",
            params={"q": PROVIDER_NAME},
            auth=AUTH,
            verify=VERIFY_SSL
        )
        provider_response.raise_for_status()
        providers = provider_response.json().get("results", [])
        for prov in providers:
            if PROVIDER_NAME in prov["display"]:
                PROVIDER_UUID = prov["uuid"]
                break
        # Get Encounter Role UUID
        role_response = requests.get(
            f"{BASE_URL}/encounterrole",
            auth=AUTH,
            verify=VERIFY_SSL
        )
        role_response.raise_for_status()
        roles = role_response.json().get("results", [])
        for role in roles:
            if role["display"] == ENCOUNTER_ROLE_NAME:
                ENCOUNTER_ROLE_UUID = role["uuid"]
                break
                
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Provider/Role-Daten: {e}")
        
    return PROVIDER_UUID, ENCOUNTER_ROLE_UUID

def get_patient_uuid(identifier):
    try:
        # Search patient by identifier
        response = requests.get(
            f"{BASE_URL}/patient",
            params={"q": identifier, "v": "default"},
            auth=AUTH,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        results = response.json().get("results", [])

        for result in results:
            # OpenMRS search can be fuzzy, check for exact identifier match if possible
            # But usually 'q' with identifier works well in OpenMRS
            return result["uuid"]
            
        print(f"Kein Patient mit dem Identifier {identifier} gefunden.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Patient-UUID: {e}")
        return None

def get_active_visit_uuid(patient_uuid, visit_type_name):
    try:
        # OpenMRS SQL-Logik: date_stopped IS NULL findet Besuche, die noch nicht abgeschlossen sind
        # REST: includeInactive=false (Standardverhalten, aber explizit besser)
        response = requests.get(
            f"{BASE_URL}/visit",
            params={
                "patient": patient_uuid,
                "includeInactive": "false",
                "v": "default"
            },
            auth=AUTH,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        visits = response.json().get("results", [])

        for visit in visits:
            if visit.get("visitType", {}).get("display") == visit_type_name:
                return visit["uuid"]

        print(f"Kein aktiver Besuch vom Typ '{visit_type_name}' für diesen Patienten gefunden.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Visit-UUID: {e}")
        return None

def get_location_uuid(location_name):
    try:
        response = requests.get(
            f"{BASE_URL}/location",
            params={"q": location_name, "v": "default"},
            auth=AUTH,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        
        for loc in results:
            if loc["display"] == location_name:
                return loc["uuid"]
        
        print(f"Keine Location mit dem Namen '{location_name}' gefunden.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Location-UUID: {e}")
        return None

def get_encounter_type_uuid(encounter_type_name):
    try:
        response = requests.get(
            f"{BASE_URL}/encountertype",
            params={"q": encounter_type_name, "v": "default"},
            auth=AUTH,
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        
        for et in results:
            if et["display"] == encounter_type_name:
                return et["uuid"]

        print(f"Kein Encounter Type mit dem Namen '{encounter_type_name}' gefunden.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der EncounterType-UUID: {e}")
        return None

def get_concept_uuid_by_name(test_names):
    orders = []
    found_names = []
    
    try:
        for name in test_names:
            response = requests.get(
                f"{BASE_URL}/concept",
                params={"q": name, "v": "default"},
                auth=AUTH,
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            
            for concept in results:
                if concept["display"] == name:
                    orders.append({
                        "concept": {
                            "uuid": concept["uuid"]
                        }
                    })
                    found_names.append(name)
                    break

        missing = set(test_names) - set(found_names)
        if missing:
            print(f"Nicht gefunden: {', '.join(missing)}")

        return orders

    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Concept-UUIDs: {e}")
        return []

def send_lab_order(data):
    try:
        print("Sende Lab Order an Bahmni...")
        response = requests.post(
            CREATE_LAB_ORDER_END_POINT, 
            json=data,        # Konvertiert dict zu JSON und setzt Header
            auth=AUTH, 
            verify=VERIFY_SSL
        )
        
        # Prüfen, ob es erfolgreich war (Status 200 oder 201)
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Erfolg! Lab Order wurde erstellt.")
            print(f"Neue Encounter-UUID: {result.get('encounterUuid')}")
            return result
        else:
            print(f"❌ Fehler: Status-Code {response.status_code}")
            print(f"Antwort vom Server: {response.text}")
            return None
            
    except Exception as e:
        print(f"Anfrage fehlgeschlagen: {e}")
        return None

if __name__ == "__main__":
    PROVIDER_NAME = "Super Man"
    ENCOUNTER_ROLE_NAME = "Unknown" # Das köntnen wir später noch ändern, aktuell gibt es nur Unknown
    PROVIDER_UUID, ENCOUNTER_ROLE_UUID = get_provider_data(PROVIDER_NAME, ENCOUNTER_ROLE_NAME)
    PROVIDERS = [{
        "encounterRoleUuid": ENCOUNTER_ROLE_UUID,
        "name": PROVIDER_NAME,
        "uuid": PROVIDER_UUID
    }]

    PATIENT_IDENTIFIER = "ABC200005"
    PATIENT_UUID = get_patient_uuid(PATIENT_IDENTIFIER)

    VISIT_TYPE_NAME = "IPD" # "OPD", "IPD", "EMERGENCY"
    VISIT_UUID = get_active_visit_uuid(PATIENT_UUID, VISIT_TYPE_NAME)

    LOCATION_NAME = "Emergency" # "OPD-1", "OPD-2", "Emergency"
    LOCATION_UUID = get_location_uuid(LOCATION_NAME)
    
    ENCOUNTER_TYPE_NAME = "Consultation" # MUSS SO SEIN
    ENCOUNTER_TYPE_UUID = get_encounter_type_uuid(ENCOUNTER_TYPE_NAME)

    ENCOUNTER_DATE_TIME = int(time.time() * 1000)

    TEST_NAMES = ["Segmentkernige"]
    ORDERS = get_concept_uuid_by_name(TEST_NAMES)

    print("providers:", PROVIDERS)
    print("patientUuid:", PATIENT_UUID)
    print("visitType:", VISIT_TYPE_NAME)
    print("visitUuid:", VISIT_UUID)
    print("locationUuid:", LOCATION_UUID)
    print("encounterTypeUuid:", ENCOUNTER_TYPE_UUID)
    print(f"encounterDateTime: {ENCOUNTER_DATE_TIME}")
    print("orders:", ORDERS)
    PAYLOAD = {
        "locationUuid": LOCATION_UUID,
        "patientUuid": PATIENT_UUID,
        "encounterUuid": None,
        "visitUuid": VISIT_UUID,
        "providers": PROVIDERS,
        "encounterDateTime": ENCOUNTER_DATE_TIME,
        "extensions":{"mdrtbSpecimen":[]},
        "context":{},
        "visitType": VISIT_TYPE_NAME,
        "bahmniDiagnoses":[],
        "orders": ORDERS,
        "drugOrders":[],
        "disposition":None,
        "observations":[],
        "encounterTypeUuid": ENCOUNTER_TYPE_UUID
    }
    send_lab_order(PAYLOAD)    

