from requests import Request, Session
import requests
from requests.auth import HTTPBasicAuth
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
PROVIDER_URL = f"{ELIS_BASE_URL}/ajaxQueryXML?provider=SampleOrderDetailsFromSampleProvider"
ACCESSION_URL = f"{ELIS_BASE_URL}/AccessionResults.do"
DASHBOARD_URL = f"{ELIS_BASE_URL}/LabDashboard.do"
ENTER_LAB_RESULT_URL = f"{ELIS_BASE_URL}/AccessionResultsUpdate.do?referer=LabDashboard"
AUTH = HTTPBasicAuth('admin', 'adminADMIN!') # Deine OpenELIS Credentials

DB_SETTINGS = {
    "dbname": "clinlims",
    "user": "clinlims",
    "password": "clinlims",
    "host": "localhost",
    "port": 5432
}

# WICHTIG: OpenELIS erwartet oft eine Session (Cookies). 
# Am besten nutzt du ein Session-Objekt:


def get_next_accession_number():
    try:
        response = requests.get(GENERATE_URL, auth=AUTH, verify=False)
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

def get_sample_ids_from_mysql(encounter_uuid, retries=5, delay=2):
    # Die SQL-Abfrage basierend auf deiner Entdeckung
    query = "SELECT id FROM sample WHERE uuid = %s AND accession_number IS NULL"
    for attempt in range(retries):
        try:
            with psycopg2.connect(**DB_SETTINGS) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (encounter_uuid,))
                    rows = cur.fetchall()
                    
                    if rows:
                        # Wir geben eine Liste von IDs zurück (z.B. [36, 37])
                        ids = [int(row[0]) for row in rows]
                        return ids
                    
            print(f"⏳ Versuch {attempt+1}: Noch kein Eintrag für UUID {encounter_uuid}. Warte {delay}s...")
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
    
    response = requests.get(url, params=params, auth=AUTH, verify=False)
    
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
    session = Session()
    session.auth = AUTH
    login_data = {
        "loginName": "admin",
        "password": "adminADMIN!"
    }
    response = session.post(LOGIN_ACTION_URL, data=login_data, verify=False)
    print(session.cookies)
    # Wir schicken einen POST an die Login-URL
    # print("Get Sample IDs...")
    # sample_ids = get_sample_ids_from_mysql("693e0656-c605-4ee8-9489-df7998c259e9")
    # print(f"Sample IDs: {sample_ids}")
    # for sample_id in sample_ids:
    #     print("Get Next Accession Number...")
    #     accession_number = get_next_accession_number()
    #     print(f"Accession Number: {accession_number}")
    #     print("Get Sample Type and Test IDs...")
    #     sample_type_and_test_ids = get_sample_type_and_test_ids(session, sample_id)
    #     sample_type_id = sample_type_and_test_ids[0]['sample_type_id']
    #     test_id = sample_type_and_test_ids[0]['test_id']
    #     print(f"Sample Type ID: {sample_type_id}")
    #     print(f"Test ID: {test_id}")
    #     print("Collect Sample...")
    #     collect_sample_rest(accession_number, test_id, sample_type_id, sample_id)
    #     print("Get Analysis ID...")
    #     analysis_id = get_analysis_id(sample_id, test_id)
    #     print(f"Analysis ID: {analysis_id}")
    #     print("Submit Test Result...")
    #     submit_test_result(analysis_id, test_id, "13", accession_number, "Blood%20Specimen")
    # hidden_fields = get_all_hidden_fields(session, "30032026-016")
    # print(hidden_fields)
    analysis_id = get_analysis_id(50, 1188)
    print(f"Analysis ID: {analysis_id}")
    submit_test_result(analysis_id, 1188, "42", "30032026-016", "Blood%20Specimen")

    # process_samples(session)
    # collect_sample_rest(accession_number, 1145, 474, 1145)
    # update_result()