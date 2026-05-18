import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost/openmrs/ws/rest/v1"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
VERIFY_SSL = False

def get_resource(endpoint, params=None):
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", auth=AUTH, params=params, verify=VERIFY_SSL)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"GET Request failed: {e}")
        return None

def post_resource(endpoint, payload):
    try:
        response = requests.post(f"{BASE_URL}/{endpoint}", auth=AUTH, json=payload, headers=HEADERS, verify=VERIFY_SSL)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Fehler bei POST {endpoint}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"POST Request failed: {e}")
        return None

def check_and_create_concept(code, display):
    if not code or not display:
        return

    # Check if term exists
    term_search = get_resource("conceptreferenceterm", {"q": code, "v": "full"})
    term_uuid = None
    if term_search and term_search.get('results'):
        for term in term_search['results']:
            if term.get('code') == code:
                term_uuid = term.get('uuid')
                break
    if not term_uuid:
        # Check source
        source_search = get_resource("conceptsource", {"q": "SNOMED-CT"})
        if source_search and source_search.get('results'):
            source_uuid = source_search['results'][0]['uuid']
        else:
            source_res = post_resource("conceptsource", {"name": "SNOMED-CT", "description": "SNOMED-CT"})
            source_uuid = source_res['uuid'] if source_res else None
            
        if source_uuid:
            term_payload = {
                "code": code,
                "name": display,
                "conceptSource": source_uuid
            }
            new_term = post_resource("conceptreferenceterm", term_payload)
            if new_term:
                term_uuid = new_term['uuid']

    if not term_uuid:
        print(f"Fehler: Konnte Term für Code {code} nicht erstellen.")
        return

    # Check if concept exists
    concept_search = get_resource("concept", {"q": code, "v": "full"})
    concept_exists = False
    if concept_search and concept_search.get('results'):
        for c in concept_search['results']:
            mappings = c.get('mappings', [])
            for m in mappings:
                ref_term = m.get('conceptReferenceTerm')
                if ref_term and isinstance(ref_term, dict):
                    if (term_uuid and ref_term.get('uuid') == term_uuid) or \
                       ref_term.get('code') == code or \
                       (code and code in ref_term.get('display', '')):
                        concept_exists = True
                        break
            if concept_exists:
                break
                
    if not concept_exists:
        datatype_search = get_resource("conceptdatatype", {"q": "N/A"})
        datatype_uuid = datatype_search['results'][0]['uuid'] if datatype_search and datatype_search.get('results') else "8d4a4c94-c2cc-11de-8d13-0010c6dffd0f"
        
        class_search = get_resource("conceptclass", {"q": "Diagnosis"})
        class_uuid = class_search['results'][0]['uuid'] if class_search and class_search.get('results') else "8d4918b0-c2cc-11de-8d13-0010c6dffd0f"
        
        concept_payload = {
            "names": [
                {"name": display, "locale": "en", "conceptNameType": "FULLY_SPECIFIED"}
            ],
            "datatype": datatype_uuid,
            "conceptClass": class_uuid,
            "mappings": [
                {
                    "conceptReferenceTerm": term_uuid,
                    "conceptMapType": "SAME-AS"
                }
            ]
        }
        new_concept = post_resource("concept", concept_payload)
        if new_concept:
            print(f"[SUCCESS] Neues Konzept erstellt: {display} (Code: {code})")
    else:
        print(f"[INFO] Konzept fuer Code {code} existiert bereits.")
    
lukas_path = r"f:\Workspace\Bahmni_Project\Patienten JSON\Lukas92_Schmidt332_e5454f04-256d-0de3-0717-03556904d434 copy.json"
lukas_path_modified = r"f:\Workspace\Bahmni_Project\Patienten JSON\Lukas92_Schmidt332_e5454f04-256d-0de3-0717-03556904d434_modified.json"

def adapt_patient_structure():
    with open(lukas_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)

    new_entries = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            # Extract basic fields
            new_resource = {
                "resourceType": resource.get("resourceType"),
                "id": resource.get("id"),
            }
            
            # Set Identifier to match Patient_02 structure
            new_resource["identifier"] = {
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
              "value": "LUKAS0001" # Geänderte ID
            }
            
            # Set active
            new_resource["active"] = True
            
            # Adapt name (remove 'use')
            new_name = []
            for n in resource.get("name", []):
                adapted_name = {
                    "family": n.get("family", ""),
                    "given": n.get("given", [])
                }
                new_name.append(adapted_name)
            new_resource["name"] = new_name
            
            # Add gender and birthDate
            new_resource["gender"] = resource.get("gender")
            new_resource["birthDate"] = resource.get("birthDate")
            
            # Adapt address (remove 'extension', 'state')
            new_address = []
            for addr in resource.get("address", []):
                adapted_addr = {
                    "line": addr.get("line", []),
                    "city": addr.get("city", ""),
                    "postalCode": addr.get("postalCode", ""),
                    "country": addr.get("country", "")
                }
                new_address.append(adapted_addr)
            new_resource["address"] = new_address
            
            entry["resource"] = new_resource
            new_entries.append(entry)
        elif resource.get("resourceType") == "Encounter":
            new_resource = {
                "resourceType": resource.get("resourceType"),
                "id": resource.get("id"),
                "status": "finished",
                "class": {
                  "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                  "code": "AMB",
                  "display": "ambulatory"
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
                  "reference": resource.get("subject", {}).get("reference"),
                  "type": "Patient"
                },
                "participant": [
                  {
                    "individual": {
                      "reference": "Practitioner/22c20629-fb23-4510-ba40-fc96ced8cbe4",
                      "type": "Practitioner"
                    }
                  }
                ],
                "period": resource.get("period", {}),
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
            entry["resource"] = new_resource
            new_entries.append(entry)
        elif resource.get("resourceType") == "Condition":
            codings = resource.get("code", {}).get("coding", [])
            
            # Check concepts via REST
            for coding in codings:
                code = coding.get("code")
                display = coding.get("display")
                if code and display:
                    check_and_create_concept(code, display)

            new_resource = {
                "resourceType": resource.get("resourceType"),
                "id": resource.get("id"),
                "clinicalStatus": resource.get("clinicalStatus"),
                "code": {
                    "coding": codings
                },
                "subject": {
                    "reference": resource.get("subject", {}).get("reference"),
                    "type": "Patient"
                },
                "encounter": {
                    "reference": resource.get("encounter", {}).get("reference"),
                    "type": "Encounter"
                },
                "recordedDate": resource.get("recordedDate"),
                "recorder": {
                    "reference": "Practitioner/22c20629-fb23-4510-ba40-fc96ced8cbe4",
                    "type": "Practitioner"
                }
            }
            entry["resource"] = new_resource
            new_entries.append(entry)
        elif resource.get("resourceType") == "Observation":
            if "subject" in resource:
                resource["subject"]["type"] = "Patient"
            if "encounter" in resource:
                resource["encounter"]["type"] = "Encounter"
            new_entries.append(entry)

    # Replace original entries with filtered ones
    bundle["entry"] = new_entries

    # Save modified JSON
    with open(lukas_path_modified, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)

    print("Patient, Encounter, Condition and Observation resources adapted/filtered successfully.")

if __name__ == "__main__":
    adapt_patient_structure()
