import requests
import os
import pandas as pd
import urllib3
import uuid 
import datetime
import json
from pathlib import Path

# SSL Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1/concept"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
VERIFY_SSL = False

def get_to_keep_laboratory_orders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Laborwerte_zum_behalten.xlsx')
    df = pd.read_excel(file_path)
    df = df.dropna()
    return df


def get_lab_samples_set_members():
    params = {'q': 'Lab Samples', 'v': 'full'} 
    response = requests.get(BASE_URL, auth=AUTH, params=params, verify=VERIFY_SSL)
    results = response.json().get('results', [])
    if not results:
        print("   ⚠️ Kein Konzept mit Namen 'Lab Samples' gefunden.")
        return
    lab_samples_backup = {
        "Lab Samples": {
            "parent_uuid": results[0].get('uuid'),
            "parent_name": results[0].get('display'),
            "set_members": []
        }
    }
    member_list = []
    members = results[0].get('setMembers', [])
    if members:
        for member in members:
            member_list.append({
                'uuid': member.get('uuid'),
                'name': member.get('display'),
                'retired': member.get('retired') # Status mit sichern
            })
        print(f"   ✅ {len(member_list)} Members gefunden.")
    else:
        print("   ℹ️ Keine Members vorhanden.")
    lab_samples_backup["Lab Samples"]["set_members"] = member_list
    return lab_samples_backup


def get_laboratory_orders(lab_samples_set_members):
    ALL_CONCEPT_NAME = [member['name'] for member in lab_samples_set_members]
    
    # Wir bauen ein Dictionary, das die Eltern-Kind-Beziehung erhält
    backup_data = {}

    print("🚀 Starte Backup-Scan der Set Members...\n")

    for laboratory_type in ALL_CONCEPT_NAME:
        print(f"🔍 Untersuche: {laboratory_type}...")
        
        # 'v': 'full' ist nötig, um setMembers Details zu sehen
        # 'includeAll': 'true' falls Sie auch retired parents finden wollen (optional)
        params = {'q': laboratory_type, 'v': 'full'} 
        
        try:
            response = requests.get(BASE_URL, auth=AUTH, params=params, verify=VERIFY_SSL)
            
            if response.status_code != 200:
                print(f"   ⚠️ Fehler beim Abruf von {laboratory_type}: {response.status_code}")
                continue # Weiter zum nächsten, nicht abbrechen

            results = response.json().get('results', [])
            if not results:
                print(f"   ⚠️ Kein Konzept mit Namen '{laboratory_type}' gefunden.")
                continue

            # Wir nehmen das erste Ergebnis (Achtung: bei Namensdopplungen evtl. prüfen)
            parent_concept = results[0]
            parent_uuid = parent_concept.get('uuid')
            members = parent_concept.get('setMembers', [])
            
            # Liste der Kinder erstellen
            member_list = []
            if members:
                for member in members:
                    member_list.append({
                        'uuid': member.get('uuid'),
                        'name': member.get('display'),
                        'retired': member.get('retired') # Status mit sichern
                    })
                print(f"   ✅ {len(member_list)} Members gefunden.")
            else:
                print("   ℹ️ Keine Members vorhanden.")

            # In das Backup Dictionary schreiben
            backup_data[laboratory_type] = {
                'parent_uuid': parent_uuid,
                'parent_name': parent_concept.get('display'),
                'set_members': member_list
            }

        except Exception as e:
            print(f"   ❌ Kritischer Fehler bei {laboratory_type}: {e}")
            continue

    return backup_data


def save_backup_to_file(data, filename_prefix):
    """
    Speichert das Dictionary in eine JSON Datei mit Zeitstempel.
    """
    if not data:
        print("❌ Keine Daten zum Speichern vorhanden.")
        return

    # Zeitstempel für eindeutigen Dateinamen
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_dir = Path(__file__).parent.resolve()
    filename = os.path.join(script_dir, "JSON", f"{filename_prefix}_{timestamp}.json")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # ensure_ascii=False sorgt dafür, dass Umlaute etc. lesbar bleiben
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*40)
        print(f"💾 Backup erfolgreich erstellt: {filename}")
        print("="*40)
        
    except IOError as e:
        print(f"❌ Fehler beim Schreiben der Datei: {e}")


def restore_from_backup(filename):
    """
    Liest eine Backup-JSON Datei ein und überschreibt die Set Members
    der darin enthaltenen Eltern-Konzepte.
    """
    # 1. Pfad zur Datei im JSON-Ordner konstruieren
    script_dir = Path(__file__).parent.resolve()
    file_path = script_dir / "JSON" / filename

    if not file_path.exists():
        print(f"❌ Fehler: Die Datei '{filename}' wurde im Ordner 'JSON' nicht gefunden.")
        return

    print(f"📂 Lese Backup Datei: {filename}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Lesen der JSON Datei: {e}")
        return

    print(f"🔄 Starte Wiederherstellung für {len(backup_data)} Konzepte...\n")

    # Header für JSON Content
    headers = {'Content-Type': 'application/json'}

    # 2. Durch alle Einträge im Backup iterieren
    for concept_name, data in backup_data.items():
        parent_uuid = data.get('parent_uuid')
        members = data.get('set_members', [])
        
        if not parent_uuid:
            print(f"⚠️ Überspringe '{concept_name}': Keine Parent-UUID im Backup.")
            continue

        # 3. Payload vorbereiten
        # OpenMRS erwartet eine Liste von Objekten, die nur die UUID enthalten müssen.
        # Format: "setMembers": [ {"uuid": "123..."}, {"uuid": "456..."} ]
        member_uuids = [{"uuid": m['uuid']} for m in members]

        payload = {
            "setMembers": member_uuids
        }

        url = f"{BASE_URL}/{parent_uuid}"
        
        print(f"   🔨 Stelle wieder her: '{concept_name}' ({len(member_uuids)} Members)...")

        try:
            # 4. POST Request zum Überschreiben
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                auth=AUTH, 
                verify=VERIFY_SSL
            )

            if response.status_code == 200:
                print(f"      ✅ Erfolg.")
            else:
                print(f"      ❌ Fehler (Status {response.status_code}): {response.text}")

        except Exception as e:
            print(f"      ❌ Verbindungsfehler: {e}")

    print("\n✅ Wiederherstellung abgeschlossen.")


def hide_obsolete_laboratory_orders(to_keep_laboratory_orders_df, all_laboratory_orders):
    for uuid, name in all_laboratory_orders.items():
        if uuid == "165981AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA":
            if uuid in to_keep_laboratory_orders_df['UUID'].values:
                continue
            print(f"Hide {name} ({uuid})...")
            stop
            retire_concept(uuid)


if __name__ == "__main__":
    # lab_samples_set_members = get_lab_samples_set_members()
    # save_backup_to_file(lab_samples_set_members, "backup_lab_samples_set_members")
    # all_laboratory_orders = get_laboratory_orders(lab_samples_set_members)
    # save_backup_to_file(all_laboratory_orders, "backup_all_lab_orders") # --> Saves the original state of all set members of all laboratory orders

    restore_from_backup("backup_lab_samples_set_members_original_state.json")
    restore_from_backup("backup_all_lab_orders_original_state.json")