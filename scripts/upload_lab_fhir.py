import csv
import requests
import json
from datetime import datetime

# --- Konfiguration ---
FHIR_BASE_URL = "https://kis-lab.mi.intern/openmrs/ws/fhir2/R4"
AUTH = ('admin', 'Admin123') # TODO: Mit deinen Bahmni-Zugangsdaten ersetzen
HEADERS = {'Content-Type': 'application/fhir+json', 'Accept': 'application/fhir+json'}
VERIFY_SSL = False 

# Variablen für unseren Durchlauf
PATIENT_IDENTIFIER = "ABC210002"
CONCEPT_UUID = "160053AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
CSV_FILE_PATH = r"C:\Users\ronja\Bahmni\KIS-Projekt\FlorianHauptmann_glucose_19-3-2026 copy.csv"


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


def create_patient(identifier_value):
    """Erstellt einen neuen Patienten und gibt die dynamisch generierte UUID zurück."""
    print("-> Patient nicht gefunden. Erstelle neuen Patienten...")
    url = f"{FHIR_BASE_URL}/Patient"
    
    patient_payload = {
        "resourceType": "Patient",
        # Keine "id" mitgeben, damit der Server sie generiert!
        "identifier": [
            {
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
                "family": "Schmidt332",
                "given": [
                    "Lukas92",
                    "Elias404"
                ]
            }
        ],
        "gender": "male",
        "birthDate": "2019-06-20",
        "deceasedBoolean": False
    }
    
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=patient_payload, verify=VERIFY_SSL)
    
    if response.status_code != 201:
        raise Exception(f"Fehler beim Erstellen des Patienten: {response.text}")
        
    patient_uuid = response.json()["id"] # Hier extrahieren wir die frisch vergebene UUID!
    print(f"-> Patient erfolgreich erstellt! Neue UUID: {patient_uuid}")
    return patient_uuid


def create_encounter(patient_uuid):
    """Erstellt einen Encounter für den Patienten."""
    print("Erstelle Encounter...")
    url = f"{FHIR_BASE_URL}/Encounter"
    
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
            "start": "2019-06-20T12:16:55+02:00",
            "end": "2019-06-20T12:31:55+02:00"
        },
        "location": [
            {
                "location": {
                    "reference": "Location/72636eba-29bf-4d6c-97c4-4b04d87a95b5",
                    "type": "Location",
                    "display": "Bahmni Hospital"
                }
            }
        ]
    }
    
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=encounter_payload, verify=VERIFY_SSL)
    response.raise_for_status()
    
    encounter_uuid = response.json()["id"]
    print(f"-> Encounter erfolgreich erstellt! UUID: {encounter_uuid}")
    return encounter_uuid


def upload_observations(patient_uuid, encounter_uuid, csv_path):
    """Liest die CSV-Datei ein und postet die Glukosewerte als Observation."""
    print("Starte CSV-Verarbeitung...")
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        lines = file.readlines()
        
        # FreeStyle Libre Metadaten überspringen (Zeile 1 weglassen)
        csv_data = lines[1:]
        reader = csv.DictReader(csv_data)
        
        success_count = 0
        
        for row in reader:
            glukose_str = row.get('Glukosewert-Verlauf mg/dL') or row.get('Glukose-Scan mg/dL')
            
            if not glukose_str or glukose_str.strip() == "":
                continue
                
            glukose_wert = float(glukose_str.replace(',', '.'))
            
            raw_date = row['Gerätezeitstempel']
            parsed_date = datetime.strptime(raw_date, "%d-%m-%Y %H:%M")
            fhir_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S+00:00") 
            
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
                    "reference": f"Patient/{patient_uuid}"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_uuid}"
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
                print(f"Fehler bei {raw_date}: Code {response.status_code} - {response.text}")
                
    print(f"-> Fertig! {success_count} Glukose-Werte wurden erfolgreich importiert.")


# --- Hauptprogramm ---
if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # 1. Patient suchen oder neu anlegen (Get-or-Create)
        pat_uuid = create_patient(PATIENT_IDENTIFIER)
        
        # 2. Encounter erstellen
        enc_uuid = create_encounter(pat_uuid)
        
        # 3. CSV verarbeiten und Werte hochladen
        upload_observations(pat_uuid, enc_uuid, CSV_FILE_PATH)
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")