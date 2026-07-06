import os
import json
import time
import glob
from pydicom import dcmread
from pydicom.uid import generate_uid
from pynetdicom import AE

# 1. DEINE ANGEPASSTEN PFADE
TRIGGER_DIR = "/var/lib/docker/volumes/bahmni-standard_mirth_pacs_data/_data/triggers"
TEMPLATE_FILE = "/home/kislab/dicom_images/gesicht_roentgen.dcm"

# 2. PACS VERBINDUNGSDATEN (dcm4chee DICOM-Port, standardmäßig 11112)
PACS_IP = "172.18.0.10"  # Die ermittelte Container-IP
PACS_PORT = 11112       # Der DICOM-Port aus docker ps
PACS_AET = "DCM4CHEE"   # Der Standard AE-Title von dcm4chee in Bahmni

def process_json_trigger(file_path):
    # JSON-Daten von Mirth einlesen
    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"\n[+] Neuer Auftrag aus Bahmni erkannt!")
    print(f"    Patienten-ID: {data['patient_id']}")
    print(f"    Accession-Nr: {data['accession_number']}")
    print(f"    Untersuchung: {data['procedure']}")

    if not os.path.exists(TEMPLATE_FILE):
        print(f"[X] FEHLER: Die Bildvorlage fehlt unter: {TEMPLATE_FILE}")
        return

    # DICOM-Vorlage laden
    print(f"[*] Lade Bildvorlage und manipuliere DICOM-Header...")
    ds = dcmread(TEMPLATE_FILE)

    # Metadaten mit den echten Bahmni-Werten überschreiben
    ds.PatientID = data["patient_id"]
    ds.PatientName = data["patient_name"] if data["patient_name"] else "Patient^Bahmni"
    ds.AccessionNumber = data["accession_number"]

    # Neue eindeutige DICOM-IDs (UIDs) generieren, damit das PACS es als neues Bild akzeptiert
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()

    # Verbindung zu dcm4chee aufbauen (DICOM C-STORE)
    ae = AE()
    ae.add_requested_context(ds.file_meta.MediaStorageSOPClassUID)

    print(f"[*] Sende manipuliertes Bild an dcm4chee ({PACS_IP}:{PACS_PORT})...")
    # JETZT MIT AE-TITLE ERWEITERT:
    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)

    if assoc.is_established:
        status = assoc.send_c_store(ds)
        assoc.release()
        print(f"[V] ERFOLG: Bild wurde erfolgreich im PACS gespeichert!")
    else:
        print("[X] FEHLER: Verbindung zum dcm4chee-DICOM-Port fehlgeschlagen. Bitte prüfen ob dcm4chee läuft.")

    # Trigger-Datei löschen, damit sie nicht doppelt verarbeitet wird
    os.remove(file_path)
    print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")

# Endlosschleife zur Ordnerüberwachung
print("=========================================")
print("=== Bahmni-PACS-Bild-Injektor aktiv ===")
print("=========================================")
print(f"Überwache Mirth-Ordner: {TRIGGER_DIR}")
print(f"Nutze Bild-Vorlage:    {TEMPLATE_FILE}")
print("Warte auf Aufträge...")

# Falls Mirth den triggers-Ordner noch nicht erstellt hat, erstellen wir ihn hier sicherheitshalber
if not os.path.exists(TRIGGER_DIR):
    try:
        os.makedirs(TRIGGER_DIR)
    except Exception as e:
        print(f"[X] Hinweis: Konnte Ordner nicht erstellen (evtl. fehlende Root-Rechte): {e}")

while True:
    for json_file in glob.glob(os.path.join(TRIGGER_DIR, "*.json")):
        try:
            process_json_trigger(json_file)
        except Exception as e:
            print(f"[X] Kritischer Fehler bei der Verarbeitung: {e}")
    time.sleep(1) # Jede Sekunde nach neuen JSON-Dateien suchen
