import os
import json
import time
import glob
from pydicom import dcmread
from pydicom.uid import generate_uid
from pynetdicom import AE
from PIL import Image

# 1. DEINE ANGEPASSTEN PFADE
TRIGGER_DIR = "/var/lib/docker/volumes/bahmni-standard_mirth_pacs_data/_data/triggers"
TEMPLATE_FILE = "/home/kislab/dicom_images/gesicht_roentgen.dcm"
IMAGE_DIR = "/home/kislab/dicom_images"

# 2. PACS VERBINDUNGSDATEN (dcm4chee DICOM-Port, standardmäßig 11112)
PACS_IP = "172.18.0.10"  # Die ermittelte Container-IP
PACS_PORT = 11112       # Der DICOM-Port aus docker ps
PACS_AET = "DCM4CHEE"   # Der Standard AE-Title von dcm4chee in Bahmni

def process_json_trigger(file_path):
    # JSON-Daten von Mirth einlesen
    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"\n[+] Neuer Auftrag aus Bahmni erkannt!")
    patient_id = data.get('patient_id', '')
    patient_name = data.get('patient_name', '')
    accession_number = data.get('accession_number', '')
    procedure = data.get('procedure', '')

    print(f"    Patienten-ID: {patient_id}")
    print(f"    Patienten-Name: {patient_name}")
    print(f"    Accession-Nr: {accession_number}")
    print(f"    Untersuchung: {procedure}")

    # PNG-Suche in IMAGE_DIR
    clean_patient_name = str(patient_name).replace(" ", "").lower()
    clean_procedure = str(procedure).replace(" ", "").lower()

    # PNGs auflisten
    png_files = []
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            if f.lower().endswith('.png'):
                png_files.append(f)
    else:
        print(f"[X] FEHLER: Bildverzeichnis existiert nicht: {IMAGE_DIR}")
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    # a) Suche nach patient_name UND procedure in Dateinamen
    found_png = None
    for f in png_files:
        clean_f = f.replace(" ", "").lower()
        if clean_patient_name and clean_procedure and (clean_patient_name in clean_f) and (clean_procedure in clean_f):
            found_png = f
            break

    # b) Wenn a nicht gefunden wurde, suche nur nach procedure
    if not found_png:
        for f in png_files:
            clean_f = f.replace(" ", "").lower()
            if clean_procedure and (clean_procedure in clean_f):
                found_png = f
                break

    if not found_png:
        print(f"[X] FEHLER: Kein passendes PNG-Bild fuer Patient '{patient_name}' und Untersuchung '{procedure}' gefunden.")
        # Trigger-Datei löschen, damit sie nicht doppelt verarbeitet wird
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    png_path = os.path.join(IMAGE_DIR, found_png)
    print(f"[+] Passendes PNG-Bild gefunden: {png_path}")

    if not os.path.exists(TEMPLATE_FILE):
        print(f"[X] FEHLER: Die Bildvorlage fehlt unter: {TEMPLATE_FILE}")
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    # DICOM-Vorlage laden
    print(f"[*] Lade Bildvorlage und manipuliere DICOM-Header...")
    ds = dcmread(TEMPLATE_FILE)

    # PNG in DICOM konvertieren (Pixeldaten und Dimensionen überschreiben)
    try:
        img = Image.open(png_path)
        img_gray = img.convert('L')
        
        ds.Rows = img_gray.height
        ds.Columns = img_gray.width
        ds.PixelData = img_gray.tobytes()
        
        # Auf 8-Bit Grayscale Metadaten anpassen
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        
        # Auf 1 Frame reduzieren (falls das Template Multi-Frame war)
        ds.NumberOfFrames = 1
        for attr in ['FrameTime', 'FrameTimeVector', 'FrameIncrementPointer']:
            if hasattr(ds, attr):
                delattr(ds, attr)
        
        if 'PlanarConfiguration' in ds:
            del ds.PlanarConfiguration
    except Exception as img_err:
        print(f"[X] FEHLER bei der PNG-Konvertierung: {img_err}")
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    # Metadaten mit den echten Bahmni-Werten überschreiben
    ds.PatientID = patient_id
    ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    ds.AccessionNumber = accession_number

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
            if os.path.exists(json_file):
                try:
                    os.remove(json_file)
                    print("[*] Trigger-Datei nach kritischem Fehler bereinigt.")
                except Exception as del_err:
                    print(f"[X] Konnte Trigger-Datei nicht loeschen: {del_err}")
    time.sleep(1) # Jede Sekunde nach neuen JSON-Dateien suchen
