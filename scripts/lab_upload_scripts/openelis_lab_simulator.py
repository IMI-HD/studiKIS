import sys
import random
import requests
from requests.auth import HTTPBasicAuth
from requests import Request, Session
import urllib3
import xml.etree.ElementTree as ET
import psycopg2
import json
import datetime
import urllib.parse
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Konfiguration
ELIS_BASE_URL = "https://localhost/openelis"
LOGIN_ACTION_URL = f"{ELIS_BASE_URL}/ValidateLogin.do?ID=null&startingRecNo=1"
GENERATE_URL = f"{ELIS_BASE_URL}/ajaxQueryXML?provider=SampleEntryGenerateScanProvider&programCode="

AUTH = HTTPBasicAuth('superman', 'Admin123')
ELIS_AUTH = HTTPBasicAuth('admin', 'adminADMIN!')

DB_SETTINGS = {
    "dbname": "clinlims",
    "user": "clinlims",
    "password": "clinlims",
    "host": "localhost",
    "port": 5432
}

def get_next_accession_number():
    try:
        response = requests.get(GENERATE_URL, auth=AUTH, verify=False)
        if response.status_code == 200:
            root = ET.fromstring(response._content)
            accession_number = root.find('formfield').text
            print(f"✅ Neue Accession Number generiert: {accession_number}")
            return accession_number
    except Exception as e:
        print(f"Fehler bei Accession-Generierung: {e}")
    return None

def get_sample_ids_from_mysql(encounter_uuid, retries=10, delay=5):
    # Neueste Samples zuerst holen
    query = "SELECT id FROM sample WHERE uuid = %s AND accession_number IS NULL ORDER BY id DESC"
    for attempt in range(retries):
        try:
            with psycopg2.connect(**DB_SETTINGS) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (encounter_uuid,))
                    rows = cur.fetchall()
                    if rows:
                        return [int(row[0]) for row in rows]
            print(f"⏳ Versuch {attempt+1}: Warte auf OpenELIS-Sync für Encounter {encounter_uuid} ({delay}s)...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Datenbankfehler: {e}")
            break
    return []

def get_sample_type_and_test_ids(session, sample_id):
    url = f"{ELIS_BASE_URL}/ajaxQueryXML"
    params = {
        "provider": "SampleTypeTestsForSampleProvider",
        "sampleId": sample_id
    }
    try:
        response = session.get(url, params=params, verify=False)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.text)
        extracted_data = []
        for sample_node in root.findall(".//sample"):
            sample_type_node = sample_node.find('sampleType')
            sample_type = sample_type_node.text if sample_type_node is not None else ""
            test_ids = [t.text for t in sample_node.findall('test') if t.text]
            if sample_type and test_ids:
                extracted_data.append({
                    "sample_type_id": sample_type,
                    "test_ids": test_ids
                })
        return extracted_data
    except Exception as e:
        print(f"❌ XML Parsing Fehler: {e}")
        return []

def get_sample_type_name(sample_type_id):
    # Dynamisch den echten Namen des Probentyps aus der Datenbank ermitteln
    query = "SELECT description FROM type_of_sample WHERE id = %s"
    try:
        with psycopg2.connect(**DB_SETTINGS) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (sample_type_id,))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
    except Exception:
        pass
    return "Blood Specimen"

def collect_all_samples_rest(accession_number, test_configurations, sample_id):
    # Alle Tests der Probe dynamisch registrieren
    tests_map = {}
    types_map = {}
    for idx, config in enumerate(test_configurations):
        tests_map[str(idx)] = ",".join(config['test_ids'])
        types_map[str(idx)] = str(config['sample_type_id'])

    type_and_test_ids = {
        "tests": tests_map,
        "types": types_map
    }
    print(f"type_and_test_ids: {type_and_test_ids}")
    params = {
        "provider": "TestUpdateWithAccessionNumberProvider",
        "accessionNumber": accession_number,
        "typeAndTestIds": json.dumps(type_and_test_ids),
        "sampleId": sample_id,
        "collectionDate": datetime.datetime.now().strftime("%d/%m/%Y")
    }

    url = f"{ELIS_BASE_URL}/ajaxQueryXML"
    response = requests.get(url, params=params, auth=AUTH, verify=False)
    return response.status_code == 200

def get_analysis_id(sample_id, test_id):
    query = "SELECT a.id FROM analysis a JOIN sample_item si ON a.sampitem_id = si.id WHERE si.samp_id = %s AND a.test_id = %s;"
    with psycopg2.connect(**DB_SETTINGS) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (sample_id, test_id))
            result = cur.fetchone()
            return int(result[0]) if result else None

def submit_test_result(session, analysis_id, test_id, result_value, accession_number, sample_type_name):
    encoded_sample_type = urllib.parse.quote(sample_type_name)
    ui_referer = f"https://localhost/openelis/AccessionResults.do?accessionNumber={accession_number}&sampleType={encoded_sample_type}&referer=LabDashboard"
    warmup_url = f"{ELIS_BASE_URL}/AccessionResults.do?accessionNumber={accession_number}&sampleType={encoded_sample_type}&referer=LabDashboard"
    
    session.get(warmup_url, verify=False)
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://localhost",
        "Referer": ui_referer
    })
    session.cookies.set("bahmni.user.location", "%7B%22name%22%3A%22Emergency%22%2C%22uuid%22%3A%22b5da9afd-b29a-4cbf-91c9-ccf2aa5f799e%22%7D", domain="localhost")
    session.cookies.set("bahmni.user", "%22superman%22", domain="localhost")

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
        ("hideShowFlag", "hidden"),
        ("testResult[1].note", ""),
        ("paging.currentPage", "1")
    ]

    files = {
        "testResult[1].uploadedFile": ("", "", "application/octet-stream")
    }

    post_url = f"{ELIS_BASE_URL}/AccessionResultsUpdate.do?referer=LabDashboard"
    req = Request('POST', post_url, data=form_data_tuples, files=files)
    prepared = session.prepare_request(req)

    try:
        response = session.send(prepared, verify=False, timeout=10)
        if response.status_code == 200:
            print(f"✅ Ergebnis {result_value} für Test ID {test_id} (Analysis {analysis_id}) verbucht!")
        else:
            print(f"❌ Fehler beim Senden für Test ID {test_id}: Status {response.status_code}")
    except Exception as e:
        print(f"Sende-Fehler: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 openelis_importer.py <encounterUuid>")
        sys.exit(1)

    encounter_uuid = sys.argv[1]
    print(f"🚀 Starte LIS-Import für Encounter: {encounter_uuid}")

    session = Session()
    session.auth = ELIS_AUTH
    login_data = {"loginName": "admin", "password": "adminADMIN!"}
    session.post(LOGIN_ACTION_URL, data=login_data, verify=False)

    sample_ids = get_sample_ids_from_mysql(encounter_uuid)
    if not sample_ids:
        print(f"❌ Keine offenen Samples für Encounter {encounter_uuid} gefunden.")
        sys.exit(0)

    for sample_id in sample_ids:
        test_configurations = get_sample_type_and_test_ids(session, sample_id)
        if not test_configurations:
            continue
        print(f"Test Konfigurationen: {test_configurations}")
        accession_number = get_next_accession_number()
        
        # Alle Tests der Probe bei OpenELIS initialisieren
        collect_all_samples_rest(accession_number, test_configurations, sample_id)

        # Über JEDEN einzelnen Test iterieren
        for config in test_configurations:
            sample_type_id = config['sample_type_id']
            sample_type_name = get_sample_type_name(sample_type_id)
            
            for test_id in config['test_ids']:
                analysis_id = get_analysis_id(sample_id, test_id)
                
                if analysis_id:
                    random_value = str(random.randint(10, 50))
                    print(f"📤 Sende Zufallswert {random_value} für Test ID {test_id} ({sample_type_name})...")
                    submit_test_result(session, analysis_id, test_id, random_value, accession_number, sample_type_name)