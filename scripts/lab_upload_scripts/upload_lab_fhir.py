import csv
import requests
import json
from datetime import datetime, timedelta
import urllib3
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Konfiguration ---
FHIR_BASE_URL = "https://kis-lab.mi.intern/openmrs/ws/fhir2/R4"
AUTH = ('superman', 'Admin123') 
HEADERS = {'Content-Type': 'application/fhir+json', 'Accept': 'application/fhir+json'}
VERIFY_SSL = False 

PATIENT_IDENTIFIER = "ABC210002"
CONCEPT_UUID = "160053AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
CSV_FILE_PATH = r"F:\Workspace\Bahmni_Project\KIS-Projekt\FlorianHauptmann_glucose_19-3-2026 copy.csv"


def get_patient_uuid(identifier):
    """Versucht, den Patienten anhand des Identifiers zu finden."""
    print(f"Suche Patient mit Identifier {identifier}...")
    url = f"{FHIR_BASE_URL}/Patient?identifier={identifier}"
    
    response = requests.get(url, auth=AUTH, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    
    bundle = response.json()
    if bundle.get("total", 0) == 0 or not bundle.get("entry"):
        return None # Nicht gefunden
        
    patient_uuid = bundle["entry"][0]["resource"]["id"]
    print(f"-> Patient gefunden! Interne UUID: {patient_uuid}")
    return patient_uuid


def create_patient(identifier_value, family_name, given_name):
    """Erstellt einen neuen Patienten und gibt die dynamisch generierte UUID zurück."""
    print("-> Patient nicht gefunden. Erstelle neuen Patienten...")
    url = f"{FHIR_BASE_URL}/Patient"
    
    patient_payload = {
        "resourceType": "Patient",
        "identifier":[ 
            {
            "extension": [
                {
                "url": "http://fhir.openmrs.org/ext/patient/identifier#location",
                "valueReference": {
                    "reference": "Location/92ab9667-4686-49af-8be8-65a4b58fc49c",
                    "type": "Location"
                }
                }
            ],
            "use": "official",
            "type": {
                "coding": [
                {
                    "code": "d3153eb0-5e07-11ef-8f7c-0242ac120002"
                }
                ],
                "text": "Patient Identifier"
            },
            "value": identifier_value
            }
        ],
        "active": True,
        "name": [
            {
                "family": family_name,
                "given": [given_name]
            }
        ],
        "gender": "male",
        "birthDate": "2019-06-20",
        "deceasedBoolean": False
    }
    
    # Wandle das Dictionary explizit in einen JSON-String um (wie im anderen Skript)
    payload_str = json.dumps(patient_payload, ensure_ascii=False)
    
    response = requests.post(url, auth=AUTH, headers=HEADERS, data=payload_str, verify=VERIFY_SSL)
    print(response.text)
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Fehler beim Erstellen des Patienten: {response.text}")
        
    patient_uuid = response.json()["id"]
    print(f"-> Patient erfolgreich erstellt! Neue UUID: {patient_uuid}")
    return patient_uuid


def create_visit(patient_uuid, encounter_date_str_start, encounter_date_str_end):
    """Erstellt einen Visit UND einen Encounter für die Verknüpfung."""
    
    # --- SCHRITT 1: VISIT ERSTELLEN ---
    visit_payload = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB"
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://fhir.openmrs.org/code-system/visit-type",
                        "code": "b7494a80-fdf9-49bb-bb40-396c47b40343",
                        "display": "IPD"
                    }
                ]
            }
        ],
        "subject": {
            "reference": f"Patient/{patient_uuid}",
            "type": "Patient"
        },
        "period": {
            "start": encounter_date_str_start,
            "end": encounter_date_str_end
        }
    }
    
    visit_resp = requests.post(f"{FHIR_BASE_URL}/Encounter", auth=AUTH, headers=HEADERS, json=visit_payload, verify=VERIFY_SSL)
    visit_resp.raise_for_status()
    visit_uuid = visit_resp.json()["id"]
    return visit_uuid

def create_encounter(patient_uuid, visit_uuid, encounter_date_str_start, encounter_date_str_end): 
    # --- SCHRITT 2: ECHTEN ENCOUNTER ERSTELLEN ---
    encounter_payload = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB"
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://fhir.openmrs.org/code-system/encounter-type",
                        "code": "d3bf1623-5e07-11ef-8f7c-0242ac120002",
                        "display": "LAB_RESULT"
                    }
                ]
            }
        ],
        "subject": {
            "reference": f"Patient/{patient_uuid}",
            "type": "Patient"
        },
        "period": {
            "start": encounter_date_str_start,
            "end": encounter_date_str_end
        },        
        "location": [
            {
                "location": {
                    "reference": "Location/b5da9afd-b29a-4cbf-91c9-ccf2aa5f799e",
                    "type": "Location",
                    "display": "Emergency"
                }
            }
        ],
        "partOf": {
            "reference": f"Encounter/{visit_uuid}",
            "type": "Encounter"
        },

    }
    
    enc_resp = requests.post(f"{FHIR_BASE_URL}/Encounter", auth=AUTH, headers=HEADERS, json=encounter_payload, verify=VERIFY_SSL)
    enc_resp.raise_for_status()
    encounter_uuid = enc_resp.json()["id"]
    
    return encounter_uuid


def upload_observations(patient_uuid, csv_path):
    """Liest die CSV-Datei ein und postet die Glukosewerte als Observation."""
    print("Starte CSV-Verarbeitung...")
    
    created_visits = {}
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        lines = file.readlines()
        
        csv_data = lines[1:]
        reader = csv.DictReader(csv_data)
        rows = list(reader)
        
        success_count = 0
        print(len(rows))
        for row in tqdm(rows, desc="Lade Observations hoch"):
            glukose_str = row.get('Glukosewert-Verlauf mg/dL') or row.get('Historic Glucose mg/dL')
            
            if not glukose_str or glukose_str.strip() == "":
                continue
                
            glukose_wert = float(glukose_str.replace(',', '.'))
            
            raw_date = row.get('Gerätezeitstempel') or row.get('Device Timestamp')
            parsed_date = datetime.strptime(raw_date, "%d-%m-%Y %H:%M")
            fhir_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S+00:00") 
            
            # Bestimme den 24h-Visit-Zeitraum für diesen Kalendertag
            visit_start = datetime(parsed_date.year, parsed_date.month, parsed_date.day)
            visit_end = visit_start + timedelta(days=1)
            visit_key = visit_start.strftime("%Y-%m-%d")
            
            if visit_key not in created_visits:
                visit_start_str = visit_start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
                visit_end_str = visit_end.strftime("%Y-%m-%dT%H:%M:%S+00:00")
                v_uuid = create_visit(patient_uuid, visit_start_str, visit_end_str)
                created_visits[visit_key] = v_uuid
            else:
                v_uuid = created_visits[visit_key]
                
            encounter_uuid = create_encounter(patient_uuid, v_uuid, fhir_date, fhir_date)
            observation_payload = {
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]
                    }
                ],
                "code": {
                    "coding": [{"code": CONCEPT_UUID, "display": "Glucose"}]
                },
                "subject": {
                    "reference": f"Patient/{patient_uuid}",
                    "type": "Patient"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_uuid}",
                    "type": "Encounter"
                },
                "effectiveDateTime": fhir_date,
                "valueQuantity": {
                    "value": glukose_wert,
                    "unit": "mg/dL",
                    "system": "http://unitsofmeasure.org",
                    "code": "mg/dL"
                }
            }
            
            url = f"{FHIR_BASE_URL}/Observation"
            response = requests.post(url, auth=AUTH, headers=HEADERS, json=observation_payload, verify=VERIFY_SSL)
            
            if response.status_code == 201:
                success_count += 1
                # print(f"Erfolg: {glukose_wert} mg/dL am {fhir_date} gespeichert.")
            else:
                tqdm.write(f"Fehler bei {raw_date}: Code {response.status_code} - {response.text}")
                
    print(f"-> Fertig! {success_count} Glukose-Werte wurden erfolgreich importiert.")


if __name__ == "__main__":
    PATIENT_IDENTIFIER = "LAB000003"
    CONCEPT_UUID = "160912AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    CSV_FLORIAN = r"Florian_Hauptmann_glucose_19-3-2026_3d.csv"
    CSV_ROBIN = r"Robin_Hefner_glucose_19-3-2026_3d.csv"
    CSV_PHILIPPA = r"Philippa_Lantwin_glucose_19-3-2026_3d.csv"
    FAMILY_NAME = CSV_PHILIPPA.split('_')[1]
    GIVEN_NAME = CSV_PHILIPPA.split('_')[0]
    try:
        # 1. Patient suchen oder neu anlegen (Get-or-Create)
        pat_uuid = create_patient(PATIENT_IDENTIFIER, FAMILY_NAME, GIVEN_NAME)
        
        # 2. CSV verarbeiten und Werte hochladen
        upload_observations(pat_uuid, CSV_PHILIPPA)
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")