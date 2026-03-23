import mysql.connector
import sys

# --- KONFIGURATION ---
# Bitte Port und Passwort prüfen (wie im vorherigen Skript)
DB_CONFIG = {
    'user': 'openmrs-user',
    'password': 'password',  # Oder 'Admin123', je nach Ihrer .env
    'host': 'localhost',
    'port': 3307,            # Ihr Docker-Mapping Port
    'database': 'openmrs'
}

TARGET_IDENTIFIER = '0001310848'

def delete_patient_strictly():
    print(f"🔌 Verbinde mit Datenbank auf Port {DB_CONFIG['port']}...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        print(f"❌ Fehler: {err}"); return

    try:
        # 1. IDs sammeln
        cursor.execute("SELECT patient_id FROM patient_identifier WHERE identifier = %s", (TARGET_IDENTIFIER,))
        row = cursor.fetchone()
        if not row: 
            print("❌ Patient nicht gefunden.")
            return
        
        patient_id = row[0]
        print(f"🎯 Gefundene Patient ID: {patient_id}")

        cursor.execute("SELECT encounter_id FROM encounter WHERE patient_id = %s", (patient_id,))
        enc_ids = [r[0] for r in cursor.fetchall()]
        
        # Hilfsfunktion für Listen-Formatierung in SQL
        def format_ids(ids): return ', '.join(['%s'] * len(ids))

        # --- LÖSCHUNG STARTEN (Strikte Reihenfolge: Blätter -> Stamm) ---

        # 1. Encounter Provider (Hängt am Encounter)
        if enc_ids:
            sql = f"DELETE FROM encounter_provider WHERE encounter_id IN ({format_ids(enc_ids)})"
            cursor.execute(sql, enc_ids)
            print(f"1. Encounter Provider gelöscht: {cursor.rowcount}")

        # 2. Observations (Hängt am Encounter & Person)
        # Erst Kinder (Gruppen), dann Eltern löschen
        cursor.execute("DELETE FROM obs WHERE obs_group_id IS NOT NULL AND person_id = %s", (patient_id,))
        cursor.execute("DELETE FROM obs WHERE person_id = %s", (patient_id,))
        print(f"2. Observations gelöscht (Clean).")

        # 3. Conditions (Hängt am Patient)
        cursor.execute("DELETE FROM conditions WHERE patient_id = %s", (patient_id,))
        print(f"3. Conditions gelöscht: {cursor.rowcount}")

        # 4. Encounter (Jetzt leer, kann weg)
        if enc_ids:
            sql = f"DELETE FROM encounter WHERE encounter_id IN ({format_ids(enc_ids)})"
            cursor.execute(sql, enc_ids)
            print(f"4. Encounters gelöscht: {cursor.rowcount}")

        # --- NEU: 5a. Visit Attributes (Hängen am Visit) ---
        # Wir müssen erst die Attribute löschen, die auf die Visits des Patienten verweisen
        cursor.execute("""DELETE FROM visit_attribute WHERE visit_id IN (SELECT visit_id FROM visit WHERE patient_id = %s)""", (patient_id,))
        print(f"5a. Visit Attributes gelöscht: {cursor.rowcount}")
        
        # 5. Visit (Hängt am Patient, Encounter sind weg)
        cursor.execute("DELETE FROM visit WHERE patient_id = %s", (patient_id,))
        print(f"5. Visits gelöscht: {cursor.rowcount}")

        # 6. Patient Identifier (Hängt am Patient)
        cursor.execute("DELETE FROM patient_identifier WHERE patient_id = %s", (patient_id,))
        print(f"6. Identifiers gelöscht: {cursor.rowcount}")

        # --- NEU: 7. Audit Log (Hängt am Patient) ---
        # Muss vor der Tabelle 'patient' gelöscht werden
        cursor.execute("DELETE FROM audit_log WHERE patient_id = %s", (patient_id,))
        print(f"7. Audit Logs gelöscht: {cursor.rowcount}")

        # 8. Patient (Hängt an Person)
        cursor.execute("DELETE FROM patient WHERE patient_id = %s", (patient_id,))
        print(f"8. Patient gelöscht: {cursor.rowcount}")

        # 9. Person Details (Namen, Adressen...)
        cursor.execute("DELETE FROM person_name WHERE person_id = %s", (patient_id,))
        cursor.execute("DELETE FROM person_address WHERE person_id = %s", (patient_id,))
        cursor.execute("DELETE FROM person_attribute WHERE person_id = %s", (patient_id,))
        print(f"9. Person Details gelöscht.")

        # 10. Person (Das Ende der Kette)
        cursor.execute("DELETE FROM person WHERE person_id = %s", (patient_id,))
        print(f"10. Person gelöscht: {cursor.rowcount}")

        conn.commit()
        print("\n✅ Sauber gelöscht! (Bitte Rebuild Search Index nicht vergessen)")

    except mysql.connector.Error as err:
        print(f"\n❌ SQL Fehler: {err}")
        conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    delete_patient_strictly()