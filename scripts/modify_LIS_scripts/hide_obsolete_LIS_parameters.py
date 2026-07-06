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
    return member_list


def update_concept_members(parent_uuid, new_member_uuids):
    """
    Hilfsfunktion: Sendet die neue Member-Liste an OpenMRS.
    """
    url = f"{BASE_URL}/{parent_uuid}"
    
    # Formatierung für OpenMRS: Liste von Objekten mit UUID
    payload_members = [{"uuid": u} for u in new_member_uuids]
    
    data = {
        "setMembers": payload_members
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=data, headers=headers, auth=AUTH, verify=VERIFY_SSL)
        if response.status_code == 200:
            return True
        else:
            print(f"      ❌ Fehler beim Update: {response.text}")
            return False
    except Exception as e:
        print(f"      ❌ Exception beim Update: {e}")
        return False

def clean_up_laboratory_concepts(df, lab_samples_set_members):
    """
    Phase 1: Bereinigt die einzelnen Labor-Sets basierend auf dem DataFrame.
    Gibt eine Liste von UUIDs zurück, die jetzt leer sind (keine Members mehr haben).
    """
    # 1. Erstellen einer Menge (Set) valider UUIDs aus dem DF für schnellen Zugriff
    # Wir stellen sicher, dass es Strings sind und keine Leerzeichen haben
    valid_uuids = set(df['UUID'].astype(str).str.strip())
    
    empty_set_uuids = [] # Hier sammeln wir Sets, die komplett leer werden

    print("🚀 PHASE 1: Bereinigung der Labor-Sets (Urine, Blood, etc.)...")
    LAB_ORDER_TYPES = [member['name'] for member in lab_samples_set_members]
    for lab_type in LAB_ORDER_TYPES:
        print(f"\n🔍 Prüfe Set: '{lab_type}'")
        
        # Abruf des aktuellen Zustands
        params = {'q': lab_type, 'v': 'full'}
        resp = requests.get(BASE_URL, params=params, auth=AUTH, verify=VERIFY_SSL)
        
        results = resp.json().get('results', [])
        if not results:
            print(f"   ⚠️ Nicht gefunden.")
            continue
            
        concept = results[0] # Das erste Ergebnis nehmen
        concept_uuid = concept['uuid']
        current_members = concept.get('setMembers', [])
        
        # --- FILTER LOGIK ---
        new_member_uuids = []
        removed_count = 0
        
        for member in current_members:
            m_uuid = member['uuid']
            m_name = member.get('display', 'Unknown')
            
            if m_uuid in valid_uuids:
                new_member_uuids.append(m_uuid)
            else:
                print(f"   🗑️ Entferne '{m_name}' (nicht im DataFrame)")
                removed_count += 1
        
        # --- UPDATE PRÜFUNG ---
        if removed_count > 0:
            print(f"   💾 Aktualisiere '{lab_type}' (Entferne {removed_count}, Behalte {len(new_member_uuids)})...")
            success = update_concept_members(concept_uuid, new_member_uuids)
            if success:
                print("      ✅ Update erfolgreich.")
        else:
            print("   ✅ Keine Änderungen nötig.")

        # --- LEER-CHECK ---
        # Wenn die neue Liste leer ist, merken wir uns die UUID dieses Sets
        if len(new_member_uuids) == 0:
            print(f"   ⚠️ Set '{lab_type}' ist nun LEER!")
            empty_set_uuids.append(concept_uuid)

    return empty_set_uuids

def clean_master_lab_samples(empty_sets_to_remove):
    """
    Phase 2: Entfernt leere Labor-Sets aus dem Master-Set "Lab Samples".
    """
    print("\n" + "="*50)
    print("🚀 PHASE 2: Bereinigung des Master-Sets 'Lab Samples'...")
    
    if not empty_sets_to_remove:
        print("✅ Keine leeren Sets gefunden. Phase 2 übersprungen.")
        return

    # 1. "Lab Samples" suchen
    params = {'q': 'Lab Samples', 'v': 'full'}
    resp = requests.get(BASE_URL, params=params, auth=AUTH, verify=VERIFY_SSL)
    results = resp.json().get('results', [])
    
    if not results:
        print("❌ 'Lab Samples' Konzept nicht gefunden!")
        return

    master_concept = results[0]
    master_uuid = master_concept['uuid']
    current_members = master_concept.get('setMembers', [])
    
    print(f"ℹ️ 'Lab Samples' hat aktuell {len(current_members)} Members.")

    # 2. Filtern
    new_master_members = []
    removed_count = 0
    
    # Wir machen aus der Liste der leeren Sets ein Set für schnellen Lookup
    uuids_to_remove_set = set(empty_sets_to_remove)

    for member in current_members:
        if member['uuid'] in uuids_to_remove_set:
            print(f"   🗑️ Entferne leeres Set: '{member.get('display')}'")
            removed_count += 1
        else:
            new_master_members.append(member['uuid'])

    # 3. Update durchführen
    if removed_count > 0:
        print(f"💾 Aktualisiere 'Lab Samples'...")
        success = update_concept_members(master_uuid, new_master_members)
        if success:
            print("   ✅ 'Lab Samples' erfolgreich bereinigt.")
    else:
        print("   ✅ Alle leeren Sets waren bereits entfernt. Keine Änderung.")

if __name__ == "__main__":
    df = get_to_keep_laboratory_orders()
    if 'df' not in locals():
        print("❌ Bitte definieren Sie 'df' bevor Sie das Skript starten.")
    else:
        # 1. Unter-Sets bereinigen und leere Sets identifizieren
        lab_samples_set_members = get_lab_samples_set_members()
        empty_sets = clean_up_laboratory_concepts(df, lab_samples_set_members)
        
        # 2. Master Set bereinigen
        clean_master_lab_samples(empty_sets)