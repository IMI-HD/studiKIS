import sys
import argparse
from list_patients_by_ward import get_connection, find_patients_by_ward, print_wards_summary
from clean_patient_data import delete_patient_strictly

# UTF-8 Encoding auf Windows-Konsole sicherstellen
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Löscht alle Patienten einer bestimmten Station oder Location (z. B. Ward, OPD, Notaufnahme)."
    )
    parser.add_argument(
        'location', 
        nargs='?', 
        default=None, 
        help="Name oder ID der Station/Location (z. B. 'OPD-1', 'Emergency', 'General Ward', 4, 6)"
    )
    parser.add_argument(
        '--list', '-l', 
        action='store_true', 
        help="Listet alle verfügbaren Stationen/Locations mit Patientenzahlen auf"
    )

    args = parser.parse_args()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if args.list:
        print_wards_summary(cursor)
        cursor.close()
        conn.close()
        return

    loc_target = args.location
    if not loc_target:
        print_wards_summary(cursor)
        print("\n💡 Tipp: Du kannst die Station oder Location auch direkt übergeben:")
        print("   python scripts/clean_patients_by_ward.py \"OPD-1\"")
        print("   python scripts/clean_patients_by_ward.py 4\n")
        try:
            loc_target = input("Stationsname oder Location-ID eingeben (oder Enter zum Abbrechen): ").strip()
        except EOFError:
            loc_target = ""

    if not loc_target:
        print("❌ Keine Station/Location angegeben.")
        cursor.close()
        conn.close()
        return

    primary_loc, patients = find_patients_by_ward(cursor, loc_target)
    cursor.close()
    conn.close()

    if not primary_loc:
        print(f"❌ Station/Location '{loc_target}' nicht gefunden.")
        print("   Verwende 'python scripts/clean_patients_by_ward.py --list' für eine Übersicht.")
        return

    if not patients:
        print(f"ℹ️ Keine Patienten an Station/Location '{primary_loc['name']}' (ID: {primary_loc['location_id']}) gefunden.")
        return

    print(f"\n📍 Location / Station: {primary_loc['name']} (ID: {primary_loc['location_id']})")
    print(f"👥 Gefundene Patienten ({len(patients)}):")
    print("-" * 80)
    for p in patients:
        info_parts = [p['assignment_type']]
        if p.get('visit_status'):
            info_parts.append(f"Besuch: {p['visit_status']}")
        if p.get('bed_number'):
            info_parts.append(f"Bett: {p['bed_number']}")
        info_str = f" [{', '.join(info_parts)}]"
        print(f"  - {p['identifier']}: {p['given_name']} {p['family_name']}{info_str}")
    print("-" * 80)

    confirm = input(f"\n⚠️ Möchtest du wirklich alle {len(patients)} Patienten von '{primary_loc['name']}' löschen? (y/n): ").strip().lower()
    if confirm == 'y':
        for p in patients:
            print(f"\n--- Lösche Patient {p['identifier']} ({p['given_name']} {p['family_name']}) ---")
            delete_patient_strictly(p['identifier'])
        print(f"\n✅ Alle Patienten von '{primary_loc['name']}' wurden verarbeitet.")
    else:
        print("❌ Vorgang abgebrochen.")


if __name__ == "__main__":
    main()
