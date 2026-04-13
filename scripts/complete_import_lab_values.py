import requests
from requests.auth import HTTPBasicAuth
from requests import Request, Session
import urllib3
import xml.etree.ElementTree as ET
import psycopg2
from psycopg2 import Error
import json
import time
import datetime
from bs4 import BeautifulSoup

# Konfiguration
ELIS_BASE_URL = "https://localhost/openelis"
LOGIN_ACTION_URL = f"{ELIS_BASE_URL}/ValidateLogin.do?ID=null&startingRecNo=1"
GENERATE_URL = f"{ELIS_BASE_URL}/ajaxQueryXML?provider=SampleEntryGenerateScanProvider&programCode="
ELIS_AUTH = HTTPBasicAuth('admin', 'adminADMIN!') # Deine OpenELIS Credentials

DB_SETTINGS = {
    "dbname": "clinlims",
    "user": "clinlims",
    "password": "clinlims",
    "host": "localhost",
    "port": 5432
}


# Credentials and Settings
BASE_URL = "https://localhost/openmrs/ws/rest/v1"
CREATE_LAB_ORDER_END_POINT = f"{BASE_URL}/bahmnicore/bahmniencounter"
AUTH = HTTPBasicAuth('superman', 'Admin123')
VERIFY_SSL = False

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- OpenMRS Funktionen ---

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


# --- OpenELIS Funktionen ---


def get_next_accession_number():
    try:
        response = requests.get(GENERATE_URL, auth=ELIS_AUTH, verify=False)
        print(response._content)
        if response.status_code == 200:
            # XML parsen
            root = ET.fromstring(response._content)
            # Den Wert im Tag <accessionNumber> suchen
            accession_number = root.find('formfield').text
            print(f"✅ Neue Accession Number generiert: {accession_number}")
            return accession_number
        else:
            print(f"❌ Fehler beim Generieren: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fehler: {e}")
        return None

def get_sample_ids_from_mysql(encounter_uuid, delay=2):
    # Die SQL-Abfrage basierend auf deiner Entdeckung
    query = "SELECT id FROM sample WHERE uuid = %s AND accession_number IS NULL"
    found = False
    while not found:
        try:
            with psycopg2.connect(**DB_SETTINGS) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (encounter_uuid,))
                    rows = cur.fetchall()
                    
                    if rows:
                        # Wir geben eine Liste von IDs zurück (z.B. [36, 37])
                        found = True
                        ids = [int(row[0]) for row in rows]
                        return ids
                    
            print(f"⏳ Noch kein Eintrag für UUID {encounter_uuid}. Warte {delay}s...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Datenbankfehler: {e}")
            break
            
    return []

def get_sample_type_and_test_ids(session, sample_id):
    """
    Fragt den SampleTypeTestsForSampleProvider ab und extrahiert IDs.
    """
    url = f"http://localhost:8052/openelis/ajaxQueryXML"
    params = {
        "provider": "SampleTypeTestsForSampleProvider",
        "sampleId": sample_id
    }
    
    try:
        # Request absenden (Session sorgt für Auth-Cookies)
        response = session.get(url, params=params, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Fehler beim Abruf: {response.status_code}")
            return []

        # XML parsen
        root = ET.fromstring(response.text)
        
        extracted_data = []
        
        # Wir suchen alle <sample> Blöcke im XML
        for sample_node in root.findall(".//sample"):
            sample_type = sample_node.find('sampleType').text
            test_id = sample_node.find('test').text
            
            extracted_data.append({
                "sample_type_id": sample_type,
                "test_id": test_id
            })
            
        if extracted_data:
            print(f"✅ Extrahiert: {len(extracted_data)} Test-Konfiguration(en).")
        return extracted_data

    except Exception as e:
        print(f"❌ XML Parsing Fehler: {e}")
        return []

def collect_sample_rest(accession_number, test_id, sample_type_id, sample_id):
    # Das JSON-Objekt für die Tests und Typen
    type_and_test_ids = {
        "tests": {"0": str(test_id)},
        "types": {"0": str(sample_type_id)}
    }
    
    # Die Parameter für den AJAX-Request
    params = {
        "provider": "TestUpdateWithAccessionNumberProvider",
        "accessionNumber": accession_number,
        "typeAndTestIds": json.dumps(type_and_test_ids),
        "sampleId": sample_id,
        "collectionDate": datetime.datetime.now().strftime("%d/%m/%Y")
    }

    url = f"{ELIS_BASE_URL}/ajaxQueryXML"
    
    response = requests.get(url, params=params, auth=ELIS_AUTH, verify=False)
    
    if response.status_code == 200:
        print(f"✅ Sample {accession_number} erfolgreich erfasst!")
        return True
    else:
        print(f"❌ Fehler beim Erfassen: {response.status_code}")
        return False

def get_analysis_id(sample_id, test_id):
    query = "SELECT a.id FROM analysis a JOIN sample_item si ON a.sampitem_id = si.id WHERE si.samp_id = %s AND a.test_id = %s;"
    with psycopg2.connect(**DB_SETTINGS) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (sample_id, test_id))
            result = cur.fetchone()
            return int(result[0]) if result else None

def submit_test_result(analysis_id, test_id, result_value, accession_number, sample_type):
    # Das sind die Felder aus deinem WebKitFormBoundary
    # Der Index [1] steht für den ersten Test in der Liste
    form_data_tuples = [
        ("searchAccession", ""),
        ("paging.currentPage", "1"),
        ("testResult[1].isModified", "true"),
        ("testResult[1].analysisId", str(analysis_id)),
        ("testResult[1].resultId", ""),
        ("testResult[1].testId", str(test_id)),
        ("testResult[1].technicianSignatureId", ""),
        ("testResult[1].testKitId", ""),
        ("testResult[1].resultLimitId", ""),
        ("testResult[1].resultType", "N"),
        ("testResult[1].valid", "true"),
        ("testResult[1].referralId", ""),
        ("testResult[1].referralCanceled", "false"),
        ("testResult[1].userChoicePending", "false"),
        ("testResult[1].isReferredOutValueChanged", "false"),
        ("totsOriginal", "0"),
        ("testResult[1].resultValue", str(result_value)),
        ("testResult[1].abnormal", "false"),
        ("testResult[1].referralId", ""),  # Duplikat wie im Log
        ("hideShowFlag", "hidden"),
        ("testResult[1].note", ""),
        ("paging.currentPage", "1")        # Zweites Mal am Ende laut Log
    ]

    # Wir müssen leere Dateien mitschicken, da OpenELIS das Feld "uploadedFile" erwartet
    files = {
        "testResult[1].uploadedFile": ("", "", "application/octet-stream")
    }
    print(f"Initialisiere Session für Accession: {accession_number}...")
    ui_referer = f"https://localhost/openelis/AccessionResults.do?accessionNumber={accession_number}&sampleType={sample_type}&referer=LabDashboard"
    warmup_url = f"{ELIS_BASE_URL}/AccessionResults.do?accessionNumber={accession_number}&sampleType={sample_type}&referer=LabDashboard"
    print(f"🔥 Wärme Session auf unter: {warmup_url}")
    session.get(warmup_url, verify=False)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://localhost",
        "Referer": ui_referer,
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    session.cookies.set("bahmni.user.location", "%7B%22name%22%3A%22Emergency%22%2C%22uuid%22%3A%22b5da9afd-b29a-4cbf-91c9-ccf2aa5f799e%22%7D", domain="localhost")
    session.cookies.set("bahmni.user", "%22superman%22", domain="localhost")
    # response = session.post(url, data=form_data_tuples, files=files, verify=False)
    post_url = f"{ELIS_BASE_URL}/AccessionResultsUpdate.do?referer=LabDashboard"
    req = Request('POST', post_url, data=form_data_tuples, files=files)
    prepared = session.prepare_request(req)


    # --- DEBUGGING START ---
    print("\n" + "="*50)
    print("DER VORBEREITETE BODY:")
    print("="*50)
    if prepared.body:
        # Dekodieren, um die Boundaries und Daten zu sehen
        print(prepared.body.decode('latin-1'))
    else:
        print("⚠️ Body ist immer noch leer! Prüfe deine form_data_tuples Variable.")
    print("="*50)
    # --- DEBUGGING END ---

    try:
        response = session.send(prepared, verify=False, timeout=10)
        print(f"Status: {response.status_code}")
        print("\n" + "="*50)
        print("DEINE GESENDETEN HEADERS:")
        print("="*50)
        for key, value in response.request.headers.items():
            print(f"{key}: {value}")
        print("="*50)

        # print(response.text)
    except Exception as e:
        print(f"Sende-Fehler: {e}")
        return None

    if response.status_code == 200:
        print(f"✅ Ergebnis {result_value} für Analysis {analysis_id} erfolgreich gesendet!")
    else:
        print(f"❌ Fehler beim Senden: {response.status_code}")

def get_all_hidden_fields(session, accession_number):
    # Exakter URL-Aufruf wie im Browser (inkl. sampleType falls bekannt)
    # Nutze hier die Accession, die du gerade bearbeitest
    url = f"https://localhost/openelis/AccessionResults.do?accessionNumber={accession_number}&referer=LabDashboard"
    
    print(f"🔍 Rufe Seite auf, um State-Daten zu sammeln: {accession_number}")
    response = session.get(url, verify=False)
    
    if "login.do" in response.url:
        print("❌ Session ungültig, wurde zum Login geleitet!")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    hidden_data = []

    # Extrahiere JEDES versteckte Input-Feld
    for tag in soup.find_all("input", {"type": "hidden"}):
        name = tag.get("name")
        value = tag.get("value", "")
        if name:
            hidden_data.append((name, value))
            
    print(f"✅ {len(hidden_data)} versteckte Felder gefunden.")
    return hidden_data

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

    TEST_NAMES = ["pO2"]
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
    result = send_lab_order(PAYLOAD)    

    session = Session()
    session.auth = ELIS_AUTH
    login_data = {
        "loginName": "admin",
        "password": "adminADMIN!"
    }
    response = session.post(LOGIN_ACTION_URL, data=login_data, verify=False)
    print(session.cookies)
    # Wir schicken einen POST an die Login-URL
    # print("Get Sample IDs...")
    sample_ids = get_sample_ids_from_mysql(result.get("encounterUuid"))
    print(f"Sample IDs: {sample_ids}")
    for sample_id in sample_ids:
        print("Get Next Accession Number...")
        accession_number = get_next_accession_number()
        print(f"Accession Number: {accession_number}")
        print("Get Sample Type and Test IDs...")
        sample_type_and_test_ids = get_sample_type_and_test_ids(session, sample_id)
        sample_type_id = sample_type_and_test_ids[0]['sample_type_id']
        test_id = sample_type_and_test_ids[0]['test_id']
        print(f"Sample Type ID: {sample_type_id}")
        print(f"Test ID: {test_id}")
        print("Collect Sample...")
        collect_sample_rest(accession_number, test_id, sample_type_id, sample_id)
        print("Get Analysis ID...")
        analysis_id = get_analysis_id(sample_id, test_id)
        print(f"Analysis ID: {analysis_id}")
        print("Submit Test Result...")
        submit_test_result(analysis_id, test_id, "69", accession_number, "Blood%20Specimen")
