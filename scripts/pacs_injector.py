import os
import io
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
    Dadurch kann Oviyam2 das Dokument direkt und ohne Ladefehler auf dem Canvas darstellen!
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
    Erstellt ein DICOM-Objekt für den Befundbericht mit gerenderten Pixeldaten
    UND dem unformatierten Befundtext im ImageComments-Tag (Tag 0020,4000).
    Dadurch kann man in Oviyam2 den Text über das 'i'-Symbol (DICOM Header) markieren und kopieren!
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

    # Befundtext als kopierbarer ImageComment & StudyComment hinterlegen
    report_ds.SpecificCharacterSet = "ISO_IR 192"
    report_ds.ImageComments = report_text
    report_ds.StudyComments = report_text

    return report_ds


def generate_report_pdf(report_text):
    """
    Erstellt ein PDF-Dokument (Bytes) aus dem übergebenen Befundtext.
    Verwendet reportlab (falls installiert) oder einen leichtgewichtigen,
    vollständig standardkonformen pure-Python-Fallback.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        textobject = c.beginText(50, height - 60)
        textobject.setFont("Courier", 10)
        textobject.setLeading(14)
        for line in report_text.splitlines():
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()
        return buffer.getvalue()
    except ImportError:
        # Robuster Fallback ohne externe Abhängigkeiten
        lines = report_text.splitlines()
        font_size = 10
        line_height = 14
        margin_left = 50
        margin_top = 780

        def escape_pdf(s):
            return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

        content_lines = ['BT', f'/F1 {font_size} Tf', f'{margin_left} {margin_top} Td']
        first = True
        for line in lines:
            safe_line = escape_pdf(line)
            if first:
                content_lines.append(f'({safe_line}) Tj')
                first = False
            else:
                content_lines.append(f'0 -{line_height} Td')
                content_lines.append(f'({safe_line}) Tj')
        content_lines.append('ET')
        stream_content = '\n'.join(content_lines).encode('latin-1', 'replace')
        stream_len = len(stream_content)

        objects = [
            b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n',
            b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n',
            b'3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 595 842] /Contents 5 0 R >>\nendobj\n',
            b'4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n',
            f'5 0 obj\n<< /Length {stream_len} >>\nstream\n'.encode('ascii') + stream_content + b'\nendstream\nendobj\n'
        ]

        header = b'%PDF-1.4\n'
        body = b''
        offsets = [0]
        curr_offset = len(header)
        for obj in objects:
            offsets.append(curr_offset)
            curr_offset += len(obj)
            body += obj

        xref_offset = curr_offset
        xref = f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode('ascii')
        for off in offsets[1:]:
            xref += f'{off:010d} 00000 n \n'.encode('ascii')

        trailer = f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n'.encode('ascii')
        return header + body + xref + trailer


def create_report_pdf_dataset(report_text, patient_id, patient_name, accession_number, study_instance_uid, procedure):
    """
    Erstellt ein DICOM Encapsulated PDF Dataset (SOP Class 1.2.840.10008.5.1.4.1.1.104.1).
    Erhält dieselbe StudyInstanceUID wie das Röntgenbild (SeriesNumber 2, Modality DOC).
    Der Text im PDF ist im Viewer / Browser selektier- und kopierbar!
    """
    ENCAPSULATED_PDF_STORAGE = "1.2.840.10008.5.1.4.1.1.104.1"
    pdf_bytes = generate_report_pdf(report_text)

    report_sop_uid = generate_uid()
    report_series_uid = generate_uid()

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = ENCAPSULATED_PDF_STORAGE
    file_meta.MediaStorageSOPInstanceUID = report_sop_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    report_ds = Dataset()
    report_ds.file_meta = file_meta
    report_ds.is_little_endian = True
    report_ds.is_implicit_VR = False

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")

    # DICOM Standard-Attribute für Encapsulated Document
    report_ds.SOPClassUID = ENCAPSULATED_PDF_STORAGE
    report_ds.SOPInstanceUID = report_sop_uid
    report_ds.StudyInstanceUID = study_instance_uid  # Identisch zum Röntgenbild!
    report_ds.SeriesInstanceUID = report_series_uid
    report_ds.SeriesNumber = 2
    report_ds.InstanceNumber = 1
    report_ds.Modality = "DOC"
    report_ds.SeriesDescription = f"Befundbericht (PDF) - {procedure}" if procedure else "Befundbericht (PDF)"
    report_ds.StudyDescription = f"Radiology Order - {procedure}" if procedure else "Radiology Order"

    report_ds.PatientID = patient_id
    report_ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    report_ds.AccessionNumber = accession_number

    report_ds.StudyDate = date_str
    report_ds.StudyTime = time_str
    report_ds.ContentDate = date_str
    report_ds.ContentTime = time_str
    report_ds.AcquisitionDateTime = f"{date_str}{time_str}"

    report_ds.BurnedInAnnotation = "YES"
    report_ds.DocumentTitle = f"Befundbericht - {procedure}" if procedure else "Befundbericht"
    report_ds.MIMETypeOfEncapsulatedDocument = "application/pdf"

    # EncapsulatedDocument muss gerade Byte-Länge haben (DICOM OB Padding)
    if len(pdf_bytes) % 2 != 0:
        pdf_bytes += b"\x00"
    report_ds.EncapsulatedDocument = pdf_bytes
    report_ds.SpecificCharacterSet = "ISO_IR 192"

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
    ds.SpecificCharacterSet = "ISO_IR 192"
    # Befundtext auch direkt am Röntgenbild als ImageComment & StudyComment hinterlegen
    ds.ImageComments = report_text
    ds.StudyComments = report_text

    # Befundbericht als darstellbares Dokument-Bild mit kopierbarem ImageComments-Tag erzeugen
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

    print(f"[*] Sende Röntgenbild und Befundbericht an dcm4chee ({PACS_IP}:{PACS_PORT})...")
    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)

    if assoc.is_established:
        # 1. Röntgenbild übertragen (mit ImageComments)
        status_img = assoc.send_c_store(ds)
        img_success = hasattr(status_img, 'Status') and status_img.Status == 0x0000
        print(f"[V] Röntgenbild übertragen (Status: {hex(status_img.Status) if hasattr(status_img, 'Status') else status_img})")

        # 2. Befundbericht-Bild übertragen (mit ImageComments)
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

def main():
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


if __name__ == "__main__":
    main()

