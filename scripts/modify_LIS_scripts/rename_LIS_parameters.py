import requests
import os
import pandas as pd
import urllib3

# SSL Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1/concept"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
VERIFY_SSL = False

def get_to_keep_laboratory_orders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Laborwerte_zum_behalten_mit_Normwerten.xlsx')
    df = pd.read_excel(file_path)
    df = df.dropna()
    return df


def update_fsn_only(df):
    """
    Iteriert durch den DataFrame und ändert NUR den Fully Specified Name (FSN).
    """
    print("🚀 Starte Update der Fully Specified Names (FSN)...")
    print("-" * 60)

    updated_count = 0
    error_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        concept_uuid = str(row['UUID']).strip()
        new_name = str(row['Neuer Name']).strip()
        
        # Sicherheitschecks
        if pd.isna(row['Neuer Name']) or new_name == "" or new_name.lower() == "nan":
            skipped_count += 1
            continue
        try:
            # 1. Konzept laden
            custom_view = "custom:(uuid,display,names:(uuid,name,display,conceptNameType,locale))"
                
            get_url = f"{BASE_URL}/{concept_uuid}"
            params = {'v': custom_view}
            response = requests.get(get_url, auth=AUTH, verify=VERIFY_SSL, params=params)
            
            if response.status_code != 200:
                print(f"❌ Fehler: Konzept {concept_uuid} nicht gefunden.")
                error_count += 1
                continue

            concept_data = response.json()
            names_list = concept_data.get('names', [])
            
            # 2. Den FSN und Short Name in der Liste suchen
            fsn_uuid = None
            current_fsn_name = None
            short_uuid = None
            current_short_name = None
            
            for n in names_list:
                # Wir suchen explizit nach FSN und SHORT
                ctype = n.get('conceptNameType')
                if ctype == 'FULLY_SPECIFIED':
                    fsn_uuid = n.get('uuid')
                    current_fsn_name = n.get('display') 
                elif ctype == 'SHORT':
                    short_uuid = n.get('uuid')
                    current_short_name = n.get('display')
            
            if not fsn_uuid:
                print(f"⚠️  Warnung: Konzept {concept_uuid} hat keinen FSN (sehr ungewöhnlich).")
                error_count += 1
                continue

            # Check: Ist etwas zu tun?
            fsn_needs_update = (current_fsn_name != new_name)
            # Short Name nur updaten wenn er existiert und anders ist
            short_needs_update = (short_uuid is not None and current_short_name != new_name)

            if not fsn_needs_update and not short_needs_update:
                print(f"ℹ️  Skippe: '{current_fsn_name}' ist bereits aktuell.")
                skipped_count += 1
                continue
            
            # --- FSN Update ---
            if fsn_needs_update:
                print(f"🔄 Ändere FSN: '{current_fsn_name}' -> '{new_name}'")
                update_url = f"{BASE_URL}/{concept_uuid}/name/{fsn_uuid}"
                payload = {"name": new_name}
                
                update_response = requests.post(
                    update_url, 
                    json=payload, 
                    auth=AUTH, 
                    verify=VERIFY_SSL, 
                    headers={'Content-Type': 'application/json'}
                )

                if update_response.status_code == 200:
                    print(f"   ✅ FSN Erfolg!")
                    updated_count += 1
                else:
                    print(f"   ❌ FSN API Fehler: {update_response.status_code} - {update_response.text}")
                    error_count += 1

            # --- Short Name Update ---
            if short_needs_update:
                print(f"🔄 Ändere Short Name: '{current_short_name}' -> '{new_name}'")
                update_url = f"{BASE_URL}/{concept_uuid}/name/{short_uuid}"
                payload = {"name": new_name}
                
                update_response = requests.post(
                    update_url, 
                    json=payload, 
                    auth=AUTH, 
                    verify=VERIFY_SSL, 
                    headers={'Content-Type': 'application/json'}
                )

                if update_response.status_code == 200:
                    print(f"   ✅ Short Name Erfolg!")
                    updated_count += 1
                else:
                    print(f"   ❌ Short Name API Fehler: {update_response.status_code} - {update_response.text}")
                    error_count += 1
        except Exception as e:
            print(f"❌ Fehler beim Update von {concept_uuid}: {str(e)}")
            error_count += 1

    print("-" * 60)
    print(f"🏁 FSN Update Fertig. Aktualisiert: {updated_count} | Fehler: {error_count} | Übersprungen: {skipped_count}")


def append_suffix_to_set_members(parent_concept_name="All_Test_and_Panels", suffix="_New"):
    """
    Holt alle Member eines Concept-Sets und hängt einen Suffix an deren FSN an.
    Beispiel: "Hemoglobin" -> "Hemoglobin_New"
    """
    print(f"🚀 Starte Massen-Umbenennung für Set: '{parent_concept_name}'")
    print(f"   Suffix: '{suffix}'")
    print("-" * 60)

    # 1. Das Eltern-Konzept suchen, um die Liste der Member zu bekommen
    try:
        # Wir brauchen 'v=full', um 'setMembers' zu sehen
        params = {'q': parent_concept_name, 'v': 'full'}
        response = requests.get(BASE_URL, params=params, auth=AUTH, verify=VERIFY_SSL)
        
        results = response.json().get('results', [])
        if not results:
            print(f"❌ Fehler: Eltern-Konzept '{parent_concept_name}' nicht gefunden.")
            return

        # Wir nehmen das erste Ergebnis als das Set
        parent_concept = results[0]
        members = parent_concept.get('setMembers', [])
        
        print(f"📦 Gefunden: {len(members)} Member im Set.")
        print("-" * 60)

    except Exception as e:
        print(f"❌ Kritischer Fehler beim Abruf des Sets: {e}")
        return

    # Zähler für die Statistik
    success_count = 0
    error_count = 0
    skip_count = 0

    # 2. Durch jeden Member iterieren
    for member in members:
        member_uuid = member.get('uuid')
        
        try:
            # 3. Details des Members laden (mit Custom View für FSN)
            # Wir müssen das Konzept einzeln abrufen, um sicher an die 'names' Liste zu kommen
            custom_view = "custom:(uuid,display,names:(uuid,name,display,conceptNameType,locale))"
            member_url = f"{BASE_URL}/{member_uuid}"
            
            mem_resp = requests.get(member_url, params={'v': custom_view}, auth=AUTH, verify=VERIFY_SSL)
            
            if mem_resp.status_code != 200:
                print(f"   ⚠️ Fehler beim Laden von {member_uuid}. Überspringe.")
                error_count += 1
                continue

            mem_data = mem_resp.json()
            names_list = mem_data.get('names', [])

            # 4. Den Fully Specified Name (FSN) finden
            target_name_uuid = None
            current_fsn = None

            # Suche FSN (Bevorzugt Englisch, aber Fallback auf jeden FSN)
            for n in names_list:
                if n.get('conceptNameType') == 'FULLY_SPECIFIED':
                    if n.get('locale') == 'en':
                        target_name_uuid = n.get('uuid')
                        current_fsn = n.get('name')
                        break
            
            # Fallback (irgendein FSN)
            if not target_name_uuid:
                for n in names_list:
                    if n.get('conceptNameType') == 'FULLY_SPECIFIED':
                        target_name_uuid = n.get('uuid')
                        current_fsn = n.get('name')
                        break
            
            if not target_name_uuid:
                print(f"   ⚠️ Kein FSN gefunden für {member_uuid}. Skip.")
                error_count += 1
                continue

            # 5. Prüfen, ob Suffix schon da ist
            if current_fsn.endswith(suffix):
                print(f"   ℹ️  Bereits erledigt: '{current_fsn}'")
                skip_count += 1
                continue

            # 6. Neuen Namen bauen
            new_name = f"{current_fsn}{suffix}"
            
            print(f"   🔄 Umbenennen: '{current_fsn}' -> '{new_name}'")

            # 7. Update senden
            update_url = f"{BASE_URL}/{member_uuid}/name/{target_name_uuid}"
            payload = {"name": new_name}
            headers = {'Content-Type': 'application/json'}

            upd_resp = requests.post(update_url, json=payload, headers=headers, auth=AUTH, verify=VERIFY_SSL)

            if upd_resp.status_code == 200:
                print(f"      ✅ Erfolg")
                success_count += 1
            else:
                print(f"      ❌ API Fehler {upd_resp.status_code}: {upd_resp.text}")
                error_count += 1

        except Exception as e:
            print(f"      ❌ Exception bei {member_uuid}: {e}")
            error_count += 1

    print("-" * 60)
    print(f"🏁 FERTIG. Erfolgreich: {success_count} | Fehler: {error_count} | Übersprungen: {skip_count}")

if __name__ == "__main__":
    # append_suffix_to_set_members()
    df = get_to_keep_laboratory_orders()
    update_fsn_only(df)