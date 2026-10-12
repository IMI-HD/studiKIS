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
import re
from bs4 import BeautifulSoup

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

def get_test_name(test_id):
    query = "SELECT name FROM clinlims.test WHERE id = %s"
    try:
        with psycopg2.connect(**DB_SETTINGS) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (test_id,))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
    except Exception:
        pass
    return f"Test {test_id}"

def get_analysis_id(sample_id, test_id):
    query = "SELECT a.id FROM analysis a JOIN sample_item si ON a.sampitem_id = si.id WHERE si.samp_id = %s AND a.test_id = %s;"
    with psycopg2.connect(**DB_SETTINGS) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (sample_id, test_id))
            result = cur.fetchone()
            return int(result[0]) if result else None

def get_test_normal_range(test_id):
    """
    Fragt die hinterlegten Grenzwerte (low_normal, high_normal, id) für eine test_id aus OpenELIS ab.
    """
    query = """
        SELECT id, low_normal, high_normal, low_valid, high_valid 
        FROM clinlims.result_limits 
        WHERE test_id = %s 
        ORDER BY id DESC 
        LIMIT 1;
    """
    try:
        with psycopg2.connect(**DB_SETTINGS) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (test_id,))
                row = cur.fetchone()
                if row:
                    limit_id, low_norm, high_norm, low_valid, high_valid = row
                    
                    def parse_val(v):
                        if v is None or str(v).lower() in ('-infinity', 'infinity', 'nan', ''):
                            return None
                        try:
                            return float(v)
                        except (ValueError, TypeError):
                            return None

                    return {
                        "limit_id": limit_id,
                        "low_normal": parse_val(low_norm),
                        "high_normal": parse_val(high_norm),
                        "low_valid": parse_val(low_valid),
                        "high_valid": parse_val(high_valid)
                    }
    except Exception as e:
        print(f"⚠️ Fehler beim Abrufen der Result Limits für Test {test_id}: {e}")
    return None

def generate_gaussian_value_from_range(normal_range, fallback_min=10, fallback_max=50):
    """
    Generiert einen normalverteilten Wert (Gauß-Verteilung) basierend auf dem Normbereich.
    Liegt mit ca. 95.45% Wahrscheinlichkeit im Normbereich [low_normal, high_normal].
    """
    if not normal_range:
        return str(random.randint(fallback_min, fallback_max))

    low = normal_range.get("low_normal")
    high = normal_range.get("high_normal")

    # Fall 1: Beidseitig begrenzter Normbereich [low, high]
    if low is not None and high is not None and low < high:
        mu = (low + high) / 2.0
        sigma = (high - low) / 4.0  # 95.45% aller Werte liegen im Intervall [mu - 2*sigma, mu + 2*sigma]
        val = random.gauss(mu, sigma)

        # Bestimme Dezimalstellen anhand der Grenzwerte
        def get_decimals(num):
            s = str(num)
            if '.' in s:
                dec = s.split('.')[1]
                if dec != '0':
                    return len(dec)
            return 0

        precision = max(get_decimals(low), get_decimals(high))
        if precision > 0:
            return f"{val:.{precision}f}"
        return str(int(round(val)))

    # Fall 2: Nur Obergrenze vorhanden (z. B. CRP < 5.0)
    elif high is not None and (low is None or low <= 0):
        mu = high * 0.4
        sigma = high * 0.2
        val = max(0.0, random.gauss(mu, sigma))
        return f"{val:.1f}"

    # Fall 3: Nur Untergrenze vorhanden (z. B. eGFR > 90)
    elif low is not None and high is None:
        mu = low * 1.15
        sigma = low * 0.08
        val = random.gauss(mu, sigma)
        return f"{val:.1f}"

    # Fall 4: Kein gültiger Bereich gefunden -> Fallback
    return str(random.randint(fallback_min, fallback_max))

def parse_accession_results_page(html_text):
    """
    Parst die AccessionResults.do Seite und ermittelt für jeden Index [1], [2], ...
    die von OpenELIS vorgegebene Reihenfolge und IDs (analysisId, testId, resultLimitId).
    """
    tests_by_index = {}
    
    # 1. BeautifulSoup Parsing
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        for tag in soup.find_all(['input', 'select', 'textarea']):
            name = tag.get('name', '')
            if name.startswith('testResult[') and '].' in name:
                idx_part, field = name.split('].', 1)
                idx_str = idx_part.replace('testResult[', '')
                if idx_str.isdigit():
                    idx = int(idx_str)
                    if idx not in tests_by_index:
                        tests_by_index[idx] = {}
                    tests_by_index[idx][field] = tag.get('value', '')
    except Exception as e:
        print(f"⚠️ BS4 Parsing Fehler: {e}")

    # 2. Fallback über Regex
    if not tests_by_index:
        pattern = re.compile(r'name=["\']testResult\[(\d+)\]\.(\w+)["\'][^>]*value=["\']([^"\']*)["\']', re.IGNORECASE)
        for match in pattern.finditer(html_text):
            idx = int(match.group(1))
            field = match.group(2)
            val = match.group(3)
            if idx not in tests_by_index:
                tests_by_index[idx] = {}
            tests_by_index[idx][field] = val

    return tests_by_index

def submit_test_results(session, accession_number, sample_type_name, sample_id=None, fallback_test_ids=None):
    """
    Lädt die Seite AccessionResults.do, liest die exakte Test-Reihenfolge von OpenELIS aus,
    generiert die Gauß-Werte passend zu jedem Test und sendet alle Ergebnisse im Batch.
    """
    encoded_sample_type = urllib.parse.quote(sample_type_name)
    ui_referer = f"https://localhost/openelis/AccessionResults.do?accessionNumber={accession_number}&sampleType={encoded_sample_type}&referer=LabDashboard"
    warmup_url = f"{ELIS_BASE_URL}/AccessionResults.do?accessionNumber={accession_number}&sampleType={encoded_sample_type}&referer=LabDashboard"
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://localhost",
        "Referer": ui_referer
    })
    session.cookies.set("bahmni.user.location", "%7B%22name%22%3A%22Emergency%22%2C%22uuid%22%3A%22b5da9afd-b29a-4cbf-91c9-ccf2aa5f799e%22%7D", domain="localhost")
    session.cookies.set("bahmni.user", "%22superman%22", domain="localhost")

    print(f"🔍 Rufe OpenELIS-Formular ab: {accession_number} ({sample_type_name})...")
    response = session.get(warmup_url, verify=False)
    if response.status_code != 200:
        print(f"❌ Fehler beim Laden des Formulars: Status {response.status_code}")
        return False

    tests_by_index = parse_accession_results_page(response.text)
    
    form_data_tuples = [
        ("searchAccession", ""),
        ("paging.currentPage", "1")
    ]
    files = {}
    test_count = 0

    if tests_by_index:
        for idx in sorted(tests_by_index.keys()):
            item = tests_by_index[idx]
            test_id = item.get("testId")
            analysis_id = item.get("analysisId")
            page_limit_id = item.get("resultLimitId", "")
            
            if not test_id:
                continue

            test_name = get_test_name(test_id)
            normal_range = get_test_normal_range(test_id)
            simulated_value = generate_gaussian_value_from_range(normal_range)
            limit_id = page_limit_id if page_limit_id else (str(normal_range.get("limit_id", "")) if normal_range else "")
            
            if normal_range and (normal_range.get("low_normal") is not None or normal_range.get("high_normal") is not None):
                range_str = f"[{normal_range.get('low_normal')}, {normal_range.get('high_normal')}]"
            else:
                range_str = "Kein Normbereich (Fallback)"

            print(f"📤 [{idx}] {test_name} (ID: {test_id}, Analysis: {analysis_id}): Wert={simulated_value} (Normbereich: {range_str}, Limit ID: {limit_id})")

            form_data_tuples.extend([
                (f"testResult[{idx}].isModified", "true"),
                (f"testResult[{idx}].analysisId", str(analysis_id)),
                (f"testResult[{idx}].resultId", ""),
                (f"testResult[{idx}].testId", str(test_id)),
                (f"testResult[{idx}].technicianSignatureId", ""),
                (f"testResult[{idx}].testKitId", ""),
                (f"testResult[{idx}].resultLimitId", str(limit_id)),
                (f"testResult[{idx}].resultType", "N"),
                (f"testResult[{idx}].valid", "true"),
                (f"testResult[{idx}].referralId", ""),
                (f"testResult[{idx}].referralCanceled", "false"),
                (f"testResult[{idx}].userChoicePending", "false"),
                (f"testResult[{idx}].isReferredOutValueChanged", "false"),
                ("totsOriginal", "0"),
                (f"testResult[{idx}].resultValue", str(simulated_value)),
                (f"testResult[{idx}].abnormal", "false"),
                (f"testResult[{idx}].referralId", ""),
                ("hideShowFlag", "hidden"),
                (f"testResult[{idx}].note", "")
            ])
            files[f"testResult[{idx}].uploadedFile"] = ("", "", "application/octet-stream")
            test_count += 1
    else:
        # Fallback falls Formular-Parsing keine Felder liefert
        print("⚠️ Formularfelder konnten nicht direkt geparst werden, nutze Fallback-IDs...")
        if fallback_test_ids and sample_id:
            for idx, test_id in enumerate(fallback_test_ids, start=1):
                analysis_id = get_analysis_id(sample_id, test_id)
                if not analysis_id:
                    continue
                test_name = get_test_name(test_id)
                normal_range = get_test_normal_range(test_id)
                simulated_value = generate_gaussian_value_from_range(normal_range)
                limit_id = str(normal_range.get("limit_id", "")) if normal_range else ""
                
                print(f"📤 [{idx}] {test_name} (ID: {test_id}, Analysis: {analysis_id}): Wert={simulated_value}")

                form_data_tuples.extend([
                    (f"testResult[{idx}].isModified", "true"),
                    (f"testResult[{idx}].analysisId", str(analysis_id)),
                    (f"testResult[{idx}].resultId", ""),
                    (f"testResult[{idx}].testId", str(test_id)),
                    (f"testResult[{idx}].technicianSignatureId", ""),
                    (f"testResult[{idx}].testKitId", ""),
                    (f"testResult[{idx}].resultLimitId", limit_id),
                    (f"testResult[{idx}].resultType", "N"),
                    (f"testResult[{idx}].valid", "true"),
                    (f"testResult[{idx}].referralId", ""),
                    (f"testResult[{idx}].referralCanceled", "false"),
                    (f"testResult[{idx}].userChoicePending", "false"),
                    (f"testResult[{idx}].isReferredOutValueChanged", "false"),
                    ("totsOriginal", "0"),
                    (f"testResult[{idx}].resultValue", str(simulated_value)),
                    (f"testResult[{idx}].abnormal", "false"),
                    (f"testResult[{idx}].referralId", ""),
                    ("hideShowFlag", "hidden"),
                    (f"testResult[{idx}].note", "")
                ])
                files[f"testResult[{idx}].uploadedFile"] = ("", "", "application/octet-stream")
                test_count += 1

    if test_count == 0:
        print("❌ Keine Tests zum Senden gefunden.")
        return False

    form_data_tuples.append(("paging.currentPage", "1"))

    post_url = f"{ELIS_BASE_URL}/AccessionResultsUpdate.do?referer=LabDashboard"
    req = Request('POST', post_url, data=form_data_tuples, files=files)
    prepared = session.prepare_request(req)

    try:
        send_response = session.send(prepared, verify=False, timeout=10)
        if send_response.status_code == 200:
            print(f"✅ {test_count} Laborwert(e) für {sample_type_name} (Accession {accession_number}) erfolgreich verbucht!")
            return True
        else:
            print(f"❌ Fehler beim Senden für {sample_type_name}: Status {send_response.status_code}")
            return False
    except Exception as e:
        print(f"Sende-Fehler: {e}")
        return False

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

        # Über JEDE Probenart / Konfiguration iterieren
        for config in test_configurations:
            sample_type_id = config['sample_type_id']
            sample_type_name = get_sample_type_name(sample_type_id)
            
            print(f"🚀 Verbuche Laborwerte für {sample_type_name} (Accession {accession_number})...")
            submit_test_results(
                session=session, 
                accession_number=accession_number, 
                sample_type_name=sample_type_name, 
                sample_id=sample_id, 
                fallback_test_ids=config['test_ids']
            )