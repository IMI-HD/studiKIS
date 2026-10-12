import sys
import argparse
from datetime import datetime
import mysql.connector

# UTF-8 Encoding auf Windows-Konsole sicherstellen
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- KONFIGURATION (analog zu clean_patient_data.py) ---
DB_CONFIG = {
    'user': 'openmrs-user',
    'password': 'password',
    'host': 'localhost',
    # 'host': 'kis-lab.mi.intern',
    'port': 3307,
    'database': 'openmrs'
}


def get_connection():
    """Stellt Verbindung zur OpenMRS MySQL Datenbank her."""
    return mysql.connector.connect(**DB_CONFIG)


def get_all_wards(cursor):
    """
    Gibt alle Stationen und Fachbereiche (Locations) im KIS zurück:
    - Bettenstationen (Wards / Admission Locations)
    - Ambulanzen & Behandlungsräume (OPD / Login Locations)
    - Relevante klinische Bereiche
    """
    sql = """
        SELECT 
            l.location_id, 
            l.name, 
            l.parent_location,
            pl.name AS parent_name,
            GROUP_CONCAT(DISTINCT lt.name ORDER BY lt.name SEPARATOR ', ') AS tags,
            (SELECT COUNT(*) FROM bed_location_map blm WHERE blm.location_id = l.location_id) AS bed_count
        FROM location l
        LEFT JOIN location pl ON l.parent_location = pl.location_id
        LEFT JOIN location_tag_map ltm ON l.location_id = ltm.location_id
        LEFT JOIN location_tag lt ON ltm.location_tag_id = lt.location_tag_id
        WHERE l.retired = 0
          AND l.location_id != 1  -- Unknown Location ausschließen
        GROUP BY l.location_id
        ORDER BY 
            CASE 
                WHEN pl.name IS NULL THEN 0 
                ELSE 1 
            END,
            COALESCE(l.parent_location, l.location_id), 
            l.location_id
    """
    cursor.execute(sql)
    return cursor.fetchall()


# Alias für semantische Klarheit
get_all_locations = get_all_wards


def resolve_ward_locations(cursor, ward_identifier):
    """
    Löst einen Stationsnamen oder eine Location-ID auf.
    Gibt die primäre Location sowie alle untergeordneten Räume/Locations rekursiv zurück.
    """
    # Prüfen, ob ID übergeben wurde
    if str(ward_identifier).strip().isdigit():
        cursor.execute("""
            SELECT location_id, name, parent_location 
            FROM location 
            WHERE location_id = %s AND retired = 0
        """, (int(ward_identifier),))
    else:
        # Exakter oder case-insensitive Match
        cursor.execute("""
            SELECT location_id, name, parent_location 
            FROM location 
            WHERE LOWER(name) = LOWER(%s) AND retired = 0
        """, (str(ward_identifier).strip(),))

    primary = cursor.fetchone()

    # Falls nicht gefunden, versuche LIKE
    if not primary and not str(ward_identifier).strip().isdigit():
        cursor.execute("""
            SELECT location_id, name, parent_location 
            FROM location 
            WHERE LOWER(name) LIKE LOWER(%s) AND retired = 0
            LIMIT 1
        """, (f"%{str(ward_identifier).strip()}%",))
        primary = cursor.fetchone()

    if not primary:
        return None, []

    # Untergeordnete Räume/Stationen rekursiv ermitteln
    try:
        cursor.execute("""
            WITH RECURSIVE loc_hierarchy AS (
                SELECT location_id, name, parent_location
                FROM location
                WHERE location_id = %s AND retired = 0
                UNION ALL
                SELECT l.location_id, l.name, l.parent_location
                FROM location l
                JOIN loc_hierarchy lh ON l.parent_location = lh.location_id
                WHERE l.retired = 0
            )
            SELECT DISTINCT location_id, name, parent_location FROM loc_hierarchy
        """, (primary['location_id'],))
        all_related_locs = cursor.fetchall()
    except Exception:
        # Fallback ohne CTE
        cursor.execute("""
            SELECT location_id, name, parent_location 
            FROM location 
            WHERE (location_id = %s OR parent_location = %s) AND retired = 0
        """, (primary['location_id'], primary['location_id']))
        all_related_locs = cursor.fetchall()

    return primary, all_related_locs


# Alias für semantische Klarheit
resolve_locations = resolve_ward_locations


def find_patients_by_ward(cursor, ward_identifier):
    """
    Findet alle Patienten, die einer Station oder Location zugewiesen oder zugeordnet sind:
    1. Aktive Bett-Zuweisung (bed_patient_assignment_map mit date_stopped IS NULL)
    2. Aktiver stationärer Inpatient-Aufnahme-Encounter (ADMISSION/TRANSFER ohne DISCHARGE)
    3. Ambulante Behandlung / Registrierung / Encounter an dieser Location (z. B. OPD, REG, Consultation)
    4. Aktiver Besuch (Visit) an dieser Location
    """
    primary_loc, related_locs = resolve_ward_locations(cursor, ward_identifier)
    if not primary_loc:
        return None, []

    loc_ids = [l['location_id'] for l in related_locs]
    format_loc_ids = ', '.join(['%s'] * len(loc_ids))

    query = f"""
    SELECT 
        p.patient_id,
        pi.identifier,
        COALESCE(pn.given_name, '') AS given_name,
        COALESCE(pn.family_name, '') AS family_name,
        pr.gender,
        TIMESTAMPDIFF(YEAR, pr.birthdate, CURDATE()) AS age,
        b.bed_number,
        COALESCE(loc_bed.name, loc_adm.name, loc_enc.name, loc_vis.name, '{primary_loc['name']}') AS location_name,
        CASE 
            WHEN bpam.bed_patient_assignment_map_id IS NOT NULL THEN 'Bett-Zuweisung'
            WHEN e_adm.encounter_id IS NOT NULL THEN 'Stationäre Aufnahme (Inpatient)'
            WHEN e_latest.encounter_id IS NOT NULL THEN CONCAT('Ambulant (', COALESCE(et_latest.name, 'Encounter'), ')')
            WHEN v_active.visit_id IS NOT NULL THEN 'Besuch (Visit)'
            ELSE 'Zugeordnet'
        END AS assignment_type,
        COALESCE(bpam.date_created, e_adm.encounter_datetime, e_latest.encounter_datetime, v_active.date_started) AS activity_time,
        COALESCE(e_adm.visit_id, e_latest.visit_id, v_active.visit_id, v_any.visit_id) AS visit_id,
        CASE
            WHEN COALESCE(v_active.visit_id, v_any.visit_id) IS NULL THEN 'Kein Besuch'
            WHEN v_active.date_stopped IS NULL AND v_active.visit_id IS NOT NULL THEN 'Aktiv'
            WHEN v_any.date_stopped IS NULL THEN 'Aktiv'
            ELSE 'Geschlossen'
        END AS visit_status
    FROM patient p
    JOIN person pr ON p.patient_id = pr.person_id
    LEFT JOIN (
        SELECT person_id, given_name, family_name
        FROM (
            SELECT person_id, given_name, family_name,
                   ROW_NUMBER() OVER(PARTITION BY person_id ORDER BY preferred DESC, person_name_id ASC) AS rn
            FROM person_name WHERE voided = 0
        ) t WHERE rn = 1
    ) pn ON p.patient_id = pn.person_id
    LEFT JOIN (
        SELECT patient_id, identifier
        FROM (
            SELECT patient_id, identifier,
                   ROW_NUMBER() OVER(PARTITION BY patient_id ORDER BY preferred DESC, patient_identifier_id ASC) AS rn
            FROM patient_identifier WHERE voided = 0
        ) t WHERE rn = 1
    ) pi ON p.patient_id = pi.patient_id

    -- 1. Aktive Bettzuweisung
    LEFT JOIN (
        SELECT bpam.bed_patient_assignment_map_id, bpam.patient_id, bpam.bed_id, bpam.date_created
        FROM (
            SELECT bpam.bed_patient_assignment_map_id, bpam.patient_id, bpam.bed_id, bpam.date_created,
                   ROW_NUMBER() OVER(PARTITION BY bpam.patient_id ORDER BY bpam.date_created DESC, bpam.bed_patient_assignment_map_id DESC) AS rn
            FROM bed_patient_assignment_map bpam
            WHERE bpam.date_stopped IS NULL AND bpam.voided = 0
        ) bpam
        WHERE bpam.rn = 1
    ) bpam ON p.patient_id = bpam.patient_id
    LEFT JOIN bed b ON bpam.bed_id = b.bed_id
    LEFT JOIN bed_location_map blm ON b.bed_id = blm.bed_id AND blm.location_id IN ({format_loc_ids})
    LEFT JOIN location loc_bed ON blm.location_id = loc_bed.location_id

    -- 2. Aktive Stationäre Aufnahme / Transfer
    LEFT JOIN (
        SELECT e.encounter_id, e.patient_id, e.location_id, e.encounter_datetime, e.visit_id
        FROM (
            SELECT e.encounter_id, e.patient_id, e.location_id, e.encounter_datetime, e.visit_id, et.name AS enc_type,
                   ROW_NUMBER() OVER(PARTITION BY e.patient_id ORDER BY e.encounter_datetime DESC, e.encounter_id DESC) AS rn
            FROM encounter e
            JOIN encounter_type et ON e.encounter_type = et.encounter_type_id
            WHERE et.name IN ('ADMISSION', 'TRANSFER', 'DISCHARGE')
              AND e.voided = 0
        ) e
        WHERE e.rn = 1 AND e.enc_type IN ('ADMISSION', 'TRANSFER') AND e.location_id IN ({format_loc_ids})
    ) e_adm ON p.patient_id = e_adm.patient_id
    LEFT JOIN location loc_adm ON e_adm.location_id = loc_adm.location_id

    -- 3. Letzter Encounter an dieser Location (OPD / Ambulant / Registrierung etc.)
    LEFT JOIN (
        SELECT e.encounter_id, e.patient_id, e.location_id, e.encounter_datetime, e.encounter_type, e.visit_id
        FROM (
            SELECT e.encounter_id, e.patient_id, e.location_id, e.encounter_datetime, e.encounter_type, e.visit_id,
                   ROW_NUMBER() OVER(PARTITION BY e.patient_id ORDER BY e.encounter_datetime DESC, e.encounter_id DESC) AS rn
            FROM encounter e
            WHERE e.location_id IN ({format_loc_ids}) AND e.voided = 0
        ) e
        WHERE e.rn = 1
    ) e_latest ON p.patient_id = e_latest.patient_id
    LEFT JOIN encounter_type et_latest ON e_latest.encounter_type = et_latest.encounter_type_id
    LEFT JOIN location loc_enc ON e_latest.location_id = loc_enc.location_id

    -- 4. Aktiver Besuch an dieser Location
    LEFT JOIN (
        SELECT v.visit_id, v.patient_id, v.location_id, v.date_started, v.date_stopped
        FROM (
            SELECT v.visit_id, v.patient_id, v.location_id, v.date_started, v.date_stopped,
                   ROW_NUMBER() OVER(PARTITION BY v.patient_id ORDER BY v.date_started DESC, v.visit_id DESC) AS rn
            FROM visit v
            WHERE v.location_id IN ({format_loc_ids}) AND v.date_stopped IS NULL AND v.voided = 0
        ) v
        WHERE v.rn = 1
    ) v_active ON p.patient_id = v_active.patient_id
    LEFT JOIN location loc_vis ON v_active.location_id = loc_vis.location_id

    -- 5. Letzter Besuch generell (für Visit-Status-Anzeige)
    LEFT JOIN (
        SELECT v.visit_id, v.patient_id, v.date_started, v.date_stopped
        FROM (
            SELECT v.visit_id, v.patient_id, v.date_started, v.date_stopped,
                   ROW_NUMBER() OVER(PARTITION BY v.patient_id ORDER BY v.date_started DESC, v.visit_id DESC) AS rn
            FROM visit v WHERE v.voided = 0
        ) v WHERE v.rn = 1
    ) v_any ON p.patient_id = v_any.patient_id

    WHERE p.voided = 0
      AND (
          blm.location_id IS NOT NULL
          OR e_adm.encounter_id IS NOT NULL
          OR e_latest.encounter_id IS NOT NULL
          OR v_active.visit_id IS NOT NULL
      )
    ORDER BY pi.identifier ASC
    """

    params = loc_ids + loc_ids + loc_ids + loc_ids
    cursor.execute(query, params)
    patients = cursor.fetchall()
    return primary_loc, patients


# Alias für semantische Klarheit
find_patients_by_location = find_patients_by_ward


def print_wards_summary(cursor):
    """Gibt eine Übersicht über alle Stationen/Locations und die Anzahl der Patienten aus."""
    locations = get_all_wards(cursor)
    print("\n" + "=" * 105)
    print("🏥 VERFÜGBARE STATIONEN & LOCATIONS (OPENMRS / BAHMNI)")
    print("=" * 105)
    print(f"{'ID':<5} | {'Name':<24} | {'Typ / Tags':<32} | {'Übergeordnet':<20} | {'Patienten':<9}")
    print("-" * 105)

    for loc in locations:
        _, patients = find_patients_by_ward(cursor, loc['location_id'])
        parent = loc['parent_name'] if loc['parent_name'] else '-'
        tags = loc['tags'] if loc['tags'] else '-'
        if len(tags) > 32:
            tags = tags[:29] + '...'
        count = len(patients)
        highlight = f"👉 {count}" if count > 0 else "0"
        print(f"{loc['location_id']:<5} | {loc['name']:<24} | {tags:<32} | {parent:<20} | {highlight:<9}")

    print("-" * 105)


def print_patient_table(primary_loc, patients):
    """Gibt die Liste der Patienten einer Station/Location formatiert aus."""
    print("\n" + "=" * 105)
    print(f"📍 LOCATION / STATION: {primary_loc['name']} (Location-ID: {primary_loc['location_id']})")
    print(f"👥 Zugeordnete Patienten aktuell: {len(patients)}")
    print("=" * 105)

    if not patients:
        print("ℹ️ Keine Patienten an dieser Location zugeordnet.")
        print("-" * 105)
        return

    print(f"{'ID':<6} | {'Identifier':<12} | {'Name':<24} | {'G/A':<6} | {'Bett':<10} | {'Aufnahme/Status':<28} | {'Besuch':<10}")
    print("-" * 105)

    for p in patients:
        full_name = f"{p['given_name']} {p['family_name']}".strip()
        gender_age = f"{p['gender'] or '?'}/{p['age'] if p['age'] is not None else '?'}"
        bed = p['bed_number'] if p['bed_number'] else '-'
        act_time = p['activity_time'].strftime('%Y-%m-%d %H:%M') if p['activity_time'] else '-'
        visit_status = p.get('visit_status', '-')
        print(f"{p['patient_id']:<6} | {p['identifier']:<12} | {full_name:<24} | {gender_age:<6} | {bed:<10} | {p['assignment_type']:<28} | {visit_status:<10}")
        print(f"       └─ Ort: {p['location_name']} | Letzte Aktivität: {act_time} | Visit ID: {p['visit_id'] or '-'}")

    print("-" * 105)
    print(f"Zusammenfassung Identifier: {', '.join([p['identifier'] for p in patients if p['identifier']])}")


def main():
    parser = argparse.ArgumentParser(
        description="Listet alle Patienten auf, die einer bestimmten Station oder Location in Bahmni/OpenMRS zugewiesen oder zugeordnet sind."
    )
    parser.add_argument(
        'ward', 
        nargs='?', 
        default=None, 
        help="Name oder ID der Station/Location (z. B. 'OPD-1', 'Emergency', 'General Ward', 4, 6)"
    )
    parser.add_argument(
        '--list-wards', '--list-locations', '-l', 
        dest='list_wards',
        action='store_true', 
        help="Listet alle verfügbaren Stationen/Locations mit Patientenzahlen auf"
    )
    parser.add_argument(
        '--all', '-a', 
        action='store_true', 
        help="Listet die Patienten aller Stationen/Locations auf"
    )

    args = parser.parse_args()

    print(f"🔌 Verbinde mit OpenMRS-Datenbank auf Port {DB_CONFIG['port']}...")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        print(f"❌ Datenbankverbindungsfehler: {err}")
        sys.exit(1)

    try:
        if args.list_wards:
            print_wards_summary(cursor)
            return

        if args.all:
            wards = get_all_wards(cursor)
            for w in wards:
                primary_loc, patients = find_patients_by_ward(cursor, w['location_id'])
                if primary_loc and patients:
                    print_patient_table(primary_loc, patients)
            return

        target_ward = args.ward

        if not target_ward:
            # Wenn keine Station übergeben wurde: Übersicht anzeigen und interaktiv fragen
            print_wards_summary(cursor)
            print("\n💡 Tipp: Du kannst die Station/Location direkt per Argument übergeben:")
            print("   python scripts/list_patients_by_ward.py \"OPD-1\"")
            print("   python scripts/list_patients_by_ward.py \"Emergency\"")
            print("   python scripts/list_patients_by_ward.py 4\n")
            try:
                target_ward = input("Bitte Stationsnamen oder Location-ID eingeben (oder Enter zum Beenden): ").strip()
            except EOFError:
                target_ward = ""

            if not target_ward:
                return

        primary_loc, patients = find_patients_by_ward(cursor, target_ward)
        if not primary_loc:
            print(f"❌ Station/Location '{target_ward}' wurde nicht gefunden.")
            print("   Verwende 'python scripts/list_patients_by_ward.py -l' für alle verfügbaren Stationen/Locations.")
            return

        print_patient_table(primary_loc, patients)

    except mysql.connector.Error as err:
        print(f"\n❌ SQL-Fehler: {err}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


if __name__ == "__main__":
    main()
