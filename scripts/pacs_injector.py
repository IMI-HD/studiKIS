import os
import json
import time
import glob
from datetime import datetime
from pydicom import dcmread
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
from pynetdicom import AE
from PIL import Image, ImageDraw, ImageFont

# 1. DEINE ANGEPASSTEN PFADE
TRIGGER_DIR = "/var/lib/docker/volumes/bahmni-standard_mirth_pacs_data/_data/triggers"
TEMPLATE_FILE = "/home/kislab/dicom_images/gesicht_roentgen.dcm"
IMAGE_DIR = "/home/kislab/dicom_images"

# 2. PACS VERBINDUNGSDATEN (dcm4chee DICOM-Port, standardmäßig 11112)
PACS_IP = "127.0.0.1"   # Da Port 11112 auf den Host weitergeleitet ist (0.0.0.0:11112->11112)
PACS_PORT = 11112       # Der DICOM-Port aus docker ps
PACS_AET = "DCM4CHEE"   # Der Standard AE-Title von dcm4chee in Bahmni

# 3. BOILERPLATE BEFUND-TEMPLATE (zum Testen; kann später durch vorgefertigte Reports ersetzt werden)
REPORT_BOILERPLATE_TEMPLATE = """============================================================
BEFUNDBERICHT RADIOLOGIE (MUSTER / BOILERPLATE)
============================================================
Patient:        {patient_name}
Patienten-ID:   {patient_id}
Auftragsnummer: {accession_number}
Untersuchung:   {procedure}
Befunddatum:    {date}
------------------------------------------------------------
KLINISCHE ANGABEN & FRAGESTELLUNG:
Ausschluss ossäre Traumafolgen / Pathologie nach Anforderung.

BEFUND:
- Regelrechte Darstellung der knöchernen Strukturen im Zielgebiet.
- Keine Fissur, Frakturlinie oder pathologische Dislokation abgrenzbar.
- Regelrechte Gelenkstellung, keine Gelenkergussbildung.
- Weichteile ohne Hinweis auf tumoröse oder entzündliche Raumforderung.

BEURTEILUNG:
Unauffälliger radiologischer Normalbefund der Untersuchung '{procedure}'.
Kein Anhalt für frische ossäre Läsionen oder akuten Interventionsbedarf.
============================================================
"""


def render_report_image(report_text, width=1200, height=1500):
    """
    Rendert den Befundtext auf ein Dokumenten-Bild (weißer Hintergrund, schwarze Schrift).
    Dadurch kann Oviyam2 das Dokument direkt über seinen Canvas darstellen!
    """
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)

    # Schriftart ermitteln (Monospace für saubere Ausrichtung)
    font = None
    candidate_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "DejaVuSansMono.ttf",
        "FreeMono.ttf",
        "Courier.ttf",
        "arial.ttf"
    ]
    for font_path in candidate_fonts:
        try:
            font = ImageFont.truetype(font_path, size=22)
            break
        except Exception:
            pass

    if font is None:
        try:
            font = ImageFont.load_default(size=20)
        except TypeError:
            font = ImageFont.load_default()

    margin_x = 50
    margin_y = 60
    draw.multiline_text((margin_x, margin_y), report_text, fill=0, font=font, spacing=8)
    return img


def create_report_image_dataset(template_file, report_text, patient_id, patient_name, accession_number, study_instance_uid, procedure):
    """
    Erstellt ein DICOM-Objekt für den Befundbericht mit gerenderten Pixeldaten.
    Erhält dieselbe StudyInstanceUID wie das Röntgenbild, aber eine eigene Serie (SeriesNumber 2).
    """
    report_img = render_report_image(report_text)
    
    report_ds = dcmread(template_file)
    report_ds.Rows = report_img.height
    report_ds.Columns = report_img.width
    report_ds.PixelData = report_img.tobytes()

    report_ds.BitsAllocated = 8
    report_ds.BitsStored = 8
    report_ds.HighBit = 7
    report_ds.PixelRepresentation = 0
    report_ds.SamplesPerPixel = 1
    report_ds.PhotometricInterpretation = "MONOCHROME2"
    report_ds.NumberOfFrames = 1

    for attr in ['FrameTime', 'FrameTimeVector', 'FrameIncrementPointer']:
        if hasattr(report_ds, attr):
            delattr(report_ds, attr)
    if 'PlanarConfiguration' in report_ds:
        del report_ds.PlanarConfiguration

    report_sop_uid = generate_uid()
    report_series_uid = generate_uid()

    report_ds.PatientID = patient_id
    report_ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    report_ds.AccessionNumber = accession_number
    report_ds.StudyInstanceUID = study_instance_uid  # Identisch zum Röntgenbild!
    report_ds.SeriesInstanceUID = report_series_uid
    report_ds.SOPInstanceUID = report_sop_uid
    if hasattr(report_ds, 'file_meta'):
        report_ds.file_meta.MediaStorageSOPInstanceUID = report_sop_uid

    report_ds.SeriesNumber = 2
    report_ds.InstanceNumber = 1
    report_ds.SeriesDescription = "Befundbericht (Dokument)"
    report_ds.StudyDescription = f"Radiology Order - {procedure}" if procedure else "Radiology Order"
    report_ds.Modality = "OT"  # Other / Dokumentation

    return report_ds


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
        for f_name in os.listdir(IMAGE_DIR):
            if f_name.lower().endswith('.png'):
                png_files.append(f_name)
    else:
        print(f"[X] FEHLER: Bildverzeichnis existiert nicht: {IMAGE_DIR}")
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    # a) Suche nach patient_name UND procedure in Dateinamen
    found_png = None
    for f_name in png_files:
        clean_f = f_name.replace(" ", "").lower()
        if clean_patient_name and clean_procedure and (clean_patient_name in clean_f) and (clean_procedure in clean_f):
            found_png = f_name
            break

    # b) Wenn a nicht gefunden wurde, suche nur nach procedure
    if not found_png:
        for f_name in png_files:
            clean_f = f_name.replace(" ", "").lower()
            if clean_procedure and (clean_procedure in clean_f):
                found_png = f_name
                break

    if not found_png:
        print(f"[X] FEHLER: Kein passendes PNG-Bild fuer Patient '{patient_name}' und Untersuchung '{procedure}' gefunden.")
        # Trigger-Datei löschen, damit sie nicht doppelt verarbeitet wird
        os.remove(file_path)
        print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")
        return

    png_path = os.path.join(IMAGE_DIR, found_png)
    print(f"[+] Passendes PNG-Bild gefunden: {png_path}")

    # Befundtext generieren (Boilerplate-Template für Testzwecke)
    # Kann später durch Laden vorgefertigter Befundberichte ersetzt werden
    report_text = REPORT_BOILERPLATE_TEMPLATE.format(
        patient_name=patient_name if patient_name else "Unbekannt",
        patient_id=patient_id if patient_id else "-",
        accession_number=accession_number if accession_number else "-",
        procedure=procedure if procedure else "Radiologische Untersuchung",
        date=datetime.now().strftime("%d.%m.%Y %H:%M")
    )
    print(f"[*] Boilerplate-Befund generiert für '{procedure}' ({patient_name})")

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

    # GEMEINSAME StudyInstanceUID generieren:
    # Das ist das Herzstueck, damit Bild und Befund in derselben Studie in Oviyam2 erscheinen!
    shared_study_uid = generate_uid()

    # Bild-Metadaten mit den echten Bahmni-Werten überschreiben
    ds.PatientID = patient_id
    ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    ds.AccessionNumber = accession_number
    ds.StudyInstanceUID = shared_study_uid
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    if hasattr(ds, 'file_meta'):
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.SeriesDescription = f"Roentgen - {procedure}" if procedure else "Roentgenbild"

    # Befund-Dokument (mit gerendertem Text) erzeugen
    report_ds = create_report_image_dataset(
        template_file=TEMPLATE_FILE,
        report_text=report_text,
        patient_id=patient_id,
        patient_name=patient_name,
        accession_number=accession_number,
        study_instance_uid=shared_study_uid,
        procedure=procedure
    )

    # Verbindung zu dcm4chee aufbauen (DICOM C-STORE)
    ae = AE(ae_title=PACS_AET)
    ae.add_requested_context(ds.file_meta.MediaStorageSOPClassUID)
    if hasattr(report_ds, 'file_meta') and report_ds.file_meta.MediaStorageSOPClassUID != ds.file_meta.MediaStorageSOPClassUID:
        ae.add_requested_context(report_ds.file_meta.MediaStorageSOPClassUID)

    print(f"[*] Sende Röntgenbild und Befundbericht-Dokument an dcm4chee ({PACS_IP}:{PACS_PORT})...")
    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)

    if assoc.is_established:
        # 1. Röntgenbild übertragen
        status_img = assoc.send_c_store(ds)
        img_success = hasattr(status_img, 'Status') and status_img.Status == 0x0000
        print(f"[V] Röntgenbild übertragen (Status: {hex(status_img.Status) if hasattr(status_img, 'Status') else status_img})")

        # 2. Befundbericht-Bild übertragen
        status_rep = assoc.send_c_store(report_ds)
        rep_success = hasattr(status_rep, 'Status') and status_rep.Status == 0x0000
        print(f"[V] Befundbericht übertragen (Status: {hex(status_rep.Status) if hasattr(status_rep, 'Status') else status_rep})")

        assoc.release()
        if (img_success or status_img) and (rep_success or status_rep):
            print(f"[V] ERFOLG: Röntgenbild und Befundbericht erfolgreich im PACS gespeichert!")
    else:
        print(f"[X] FEHLER: Verbindung zu dcm4chee ({PACS_IP}:{PACS_PORT}) fehlgeschlagen.")
        if hasattr(assoc, 'is_rejected') and assoc.is_rejected:
            print(f"    Grund: DICOM Association wurde vom PACS abgewiesen (Result: {getattr(assoc, 'result', 'Rejected')}).")
        elif hasattr(assoc, 'is_aborted') and assoc.is_aborted:
            print("    Grund: DICOM Association wurde abgebrochen (Aborted).")
        else:
            print(f"    Grund: Kein TCP-Verbindungsaufbau zu {PACS_IP}:{PACS_PORT} möglich.")

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
