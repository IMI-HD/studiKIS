import csv
import requests
import json
from datetime import datetime, timedelta
import urllib3

# Warnungen unterdrücken (für lokale Entwicklung mit selbstsignierten Zertifikaten)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Konfiguration ---
FHIR_BASE_URL = "https://localhost/openmrs/ws/fhir2/R4"
AUTH = ('superman', 'Admin123') # TODO: Mit deinen Bahmni-Zugangsdaten ersetzen
HEADERS = {'Content-Type': 'application/fhir+json', 'Accept': 'application/fhir+json'}
VERIFY_SSL = False 

# Variablen für unseren Durchlauf
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


def create_patient(identifier_value):
    """Erstellt einen neuen Patienten und gibt die dynamisch generierte UUID zurück."""
    print("-> Patient nicht gefunden. Erstelle neuen Patienten...")
    url = f"{FHIR_BASE_URL}/Patient"
    
    patient_payload = {
        "resourceType": "Patient",
        # "id": "e5454f04-256d-0de3-0717-03556904d434", # Bei POST darf/muss die ID vom Server generiert werden
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
    
    # Wandle das Dictionary explizit in einen JSON-String um (wie im anderen Skript)
    payload_str = json.dumps(patient_payload, ensure_ascii=False)
    
    # Nutze data= statt json=
    response = requests.post(url, auth=AUTH, headers=HEADERS, data=payload_str, verify=VERIFY_SSL)
    print(response.text)
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Fehler beim Erstellen des Patienten: {response.text}")
        
    patient_uuid = response.json()["id"] # Hier extrahieren wir die frisch vergebene UUID!
    print(f"-> Patient erfolgreich erstellt! Neue UUID: {patient_uuid}")
    return patient_uuid


def create_visit(patient_uuid, encounter_date_str_start, encounter_date_str_end):
    """Erstellt einen Visit UND einen Encounter für die Verknüpfung."""
    
    # --- SCHRITT 1: VISIT ERSTELLEN ---
    print("Erstelle Visit...")
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
        # Den Zeitraum großzügig setzen, damit alle CSV-Werte abgedeckt sind
        "period": {
            "start": encounter_date_str_start,
            "end": encounter_date_str_end
        }
    }
    
    visit_resp = requests.post(f"{FHIR_BASE_URL}/Encounter", auth=AUTH, headers=HEADERS, json=visit_payload, verify=VERIFY_SSL)
    visit_resp.raise_for_status()
    visit_uuid = visit_resp.json()["id"]
    print(f"-> Visit erstellt! UUID: {visit_uuid}")
    return visit_uuid

def create_encounter(patient_uuid, visit_uuid, encounter_date_str_start, encounter_date_str_end): 
    # --- SCHRITT 2: ECHTEN ENCOUNTER ERSTELLEN ---
    print("Erstelle echten Encounter im Visit...")
    encounter_payload = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB"
        },
        # WICHTIG: Hier sagen wir FHIR, dass dieser Encounter ZUM VISIT gehört.
        # Dadurch weiß OpenMRS, dass es einen 'Encounter' und keinen 'Visit' anlegen soll.
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
    print(f"-> Echter Encounter erstellt! UUID: {encounter_uuid}")
    
    # Wir geben die Encounter-UUID an die Observation-Funktion weiter!
    return encounter_uuid


def upload_observations(patient_uuid, visit_uuid, csv_path):
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
            encounter_uuid = create_encounter(patient_uuid, visit_uuid, fhir_date, fhir_date)
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
                print(f"Fehler bei {raw_date}: Code {response.status_code} - {response.text}")
                
    print(f"-> Fertig! {success_count} Glukose-Werte wurden erfolgreich importiert.")


# --- Hauptprogramm ---
if __name__ == "__main__":
    try:
        # 1. Patient suchen oder neu anlegen (Get-or-Create)
        pat_uuid = create_patient(PATIENT_IDENTIFIER)
        
        # 2. CSV-Zeitraum für den Encounter ermitteln
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as file:
            lines = file.readlines()
            if len(lines) < 3:
                raise Exception("CSV-Datei ist zu kurz (Metadaten + Header + min. 1 Datenzeile erforderlich).")
            
            # FreeStyle Libre: Zeile 0 = Metadaten, Zeile 1 = Header
            csv_data = lines[1:]
            reader = list(csv.DictReader(csv_data))
            
            if not reader:
                raise Exception("Keine Datenzeilen in der CSV gefunden.")

            # Erster und letzter Zeitstempel aus der CSV lesen für den Encounter
            raw_date_start = reader[0]["Gerätezeitstempel"]
            parsed_date_start = datetime.strptime(raw_date_start, "%d-%m-%Y %H:%M") - timedelta(hours=1)
            encounter_date_str_start = parsed_date_start.strftime("%Y-%m-%dT%H:%M:%S+00:00") 

            raw_date_end = reader[-1]["Gerätezeitstempel"]
            parsed_date_end = datetime.strptime(raw_date_end, "%d-%m-%Y %H:%M") + timedelta(hours=1)
            encounter_date_str_end = parsed_date_end.strftime("%Y-%m-%dT%H:%M:%S+00:00") 

            # Encounter erstellen
            visit_uuid = create_visit(pat_uuid, encounter_date_str_start, encounter_date_str_end)
        
        # 3. CSV verarbeiten und Werte hochladen
        upload_observations(pat_uuid, visit_uuid, CSV_FILE_PATH)
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")