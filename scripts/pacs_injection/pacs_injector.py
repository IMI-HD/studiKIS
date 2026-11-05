import os
import io
import json
import time
import glob
import re
from datetime import datetime
from pydicom import dcmread
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
from pynetdicom import AE
from PIL import Image, ImageDraw, ImageFont
import requests
import urllib3
from openmrs_report import (publish_report_for_order, finding_exists_for_order, REPORT_CONCEPT_NAME,
                            OPENMRS_REST_URL, OPENMRS_AUTH)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 1. DEINE ANGEPASSTEN PFADE
TRIGGER_DIR = "/var/lib/docker/volumes/bahmni-standard_mirth_pacs_data/_data/triggers"
TEMPLATE_FILE = "/home/kislab/dicom_images/gesicht_roentgen.dcm"
IMAGE_DIR = "/home/kislab/dicom_images"
# Fall-Konfiguration (Station + Geburtsdatum -> vorgefertigte Bildgebung). Bildpfade darin relativ zu IMAGE_DIR.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CASES_FILE = os.path.join(SCRIPT_DIR, "cases.json")
# Befundtexte der Fälle ("report" in cases.json) liegen versioniert im Repo
REPORTS_DIR = os.path.join(SCRIPT_DIR, "reports")
# Unauffällige Standardbefunde für alle Orders ohne vorgefertigten Fall
DEFAULT_REPORTS_FILE = os.path.join(SCRIPT_DIR, "default_reports.json")
VIDEO_MAX_WIDTH = 1024  # MP4 werden für unkomprimiertes Multi-Frame-DICOM auf diese Breite verkleinert

# 2. PACS VERBINDUNGSDATEN (dcm4chee DICOM-Port, standardmäßig 11112)
PACS_IP = "127.0.0.1"   # Da Port 11112 auf den Host weitergeleitet ist (0.0.0.0:11112->11112)
PACS_PORT = 11112       # Der DICOM-Port aus docker ps
PACS_AET = "DCM4CHEE"   # Der Standard AE-Title von dcm4chee in Bahmni

# OpenMRS REST: URL und Zugangsdaten kommen aus openmrs_report.py
# (Geburtsdatum + Station stehen NICHT in der HL7-Nachricht und werden nachgeladen)

# 3. BOILERPLATE BEFUND-TEMPLATE (zum Testen; kann später durch vorgefertigte Reports ersetzt werden)
REPORT_BOILERPLATE_TEMPLATE = """Untersuchung: {procedure}

Befund: Regelrechte Darstellung der abgebildeten Strukturen. Kein Nachweis einer akuten oder pathologischen Veränderung.

Beurteilung: Unauffälliger Befund."""


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


def normalize_dob(dob_str):
    """Normalisiert beliebige Datumsformate (1951-06-23, 19510623, 23.06.1951) zu YYYYMMDD."""
    if not dob_str:
        return ""
    digits = re.sub(r'[^0-9]', '', str(dob_str))
    if len(digits) >= 8:
        if digits.startswith("19") or digits.startswith("20"):
            return digits[:8]
        else:
            day = digits[:2]
            month = digits[2:4]
            year = digits[4:8]
            return f"{year}{month}{day}"
    return digits


def openmrs_get(path, params=None):
    response = requests.get(
        f"{OPENMRS_REST_URL}/{path}",
        params=params,
        auth=OPENMRS_AUTH,
        headers={"Accept": "application/json"},
        verify=False,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def lookup_patient_context(patient_identifier, accession_number):
    """
    Holt Geburtsdatum, Station sowie Patient- und Order-UUID aus OpenMRS.
    Station = Location des Encounters, in dem die Radiologie-Order angelegt wurde
    (entspricht encounterData.locationName im Lab-Channel von Mirth).
    """
    ctx = {"dob": "", "ward": "", "patient_uuid": None, "order_uuid": None}

    patients = openmrs_get("patient", {
        "identifier": patient_identifier,
        "v": "custom:(uuid,person:(birthdate))"
    }).get("results", [])
    if not patients:
        print(f"[!] Patient '{patient_identifier}' nicht in OpenMRS gefunden.")
        return ctx

    patient_uuid = patients[0]["uuid"]
    ctx["patient_uuid"] = patient_uuid
    ctx["dob"] = ((patients[0].get("person") or {}).get("birthdate") or "")[:10]  # "1951-06-23"

    # a) Order und deren Encounter über die Accession-/Order-Nummer finden
    encounter_uuid = None
    orders = openmrs_get("order", {
        "patient": patient_uuid,
        "v": "custom:(uuid,orderNumber,accessionNumber,encounter:(uuid))"
    }).get("results", [])
    for order in orders:
        if accession_number and accession_number in (order.get("orderNumber"), order.get("accessionNumber")):
            ctx["order_uuid"] = order["uuid"]
            encounter_uuid = (order.get("encounter") or {}).get("uuid")
            break

    if encounter_uuid:
        encounter = openmrs_get(f"encounter/{encounter_uuid}", {"v": "custom:(location:(display))"})
        ctx["ward"] = (encounter.get("location") or {}).get("display") or ""
    else:
        # b) Fallback: Location des jüngsten Encounters des Patienten
        print(f"[!] Keine Order zu Accession '{accession_number}' gefunden -> nutze jüngsten Encounter.")
        encounters = openmrs_get("encounter", {
            "patient": patient_uuid,
            "v": "custom:(encounterDatetime,location:(display))"
        }).get("results", [])
        latest = max(encounters, key=lambda e: e.get("encounterDatetime") or "", default={})
        ctx["ward"] = (latest.get("location") or {}).get("display") or ""

    return ctx


def load_cases(cases_file):
    """
    Lädt die Fall-Konfiguration. Wird bei JEDEM Auftrag neu gelesen,
    d.h. neue Fälle/Bilder sind ohne Neustart des Injektors aktiv.
    """
    if not os.path.exists(cases_file):
        print(f"[!] Keine Fall-Konfiguration gefunden: {cases_file}")
        return []
    with open(cases_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def matches_procedure(keywords, procedure):
    """True, wenn eines der Stichwörter im Untersuchungsnamen vorkommt (Groß-/Kleinschreibung egal)."""
    if isinstance(keywords, str):
        keywords = [keywords]
    procedure_lower = str(procedure or "").strip().lower()
    return any(k.strip().lower() in procedure_lower for k in keywords if k.strip())


def find_case_study(cases, ward, dob, procedure):
    """
    Sucht den Fall, dessen Station (Teilstring) UND Geburtsdatum passen,
    und darin die Untersuchung, deren Stichwort im Untersuchungsnamen vorkommt.
    """
    norm_dob = normalize_dob(dob)
    ward_lower = str(ward or "").strip().lower()
    if not norm_dob or not ward_lower:
        return None, None

    for case in cases:
        case_ward = str(case.get('ward', '')).strip().lower()
        if normalize_dob(case.get('dob')) != norm_dob or not case_ward or case_ward not in ward_lower:
            continue
        for study in case.get('studies', []):
            if matches_procedure(study.get('procedure', []), procedure):
                return case, study
    return None, None


def find_default_report(procedure):
    """
    Unauffälliger Standardbefund aus default_reports.json: erste Regel, deren Stichwort passt.
    Eine Regel ohne "procedure" passt immer (allgemeiner Normalbefund, gehört ans Ende).
    """
    for rule in load_cases(DEFAULT_REPORTS_FILE):
        keywords = rule.get('procedure')
        if not keywords or matches_procedure(keywords, procedure):
            return rule
    return None


def find_legacy_png(patient_name, procedure):
    """
    Bisherige Suche: PNG in IMAGE_DIR, dessen Dateiname Patientenname und/oder Untersuchung enthält.
    """
    clean_patient_name = str(patient_name).replace(" ", "").lower()
    clean_procedure = str(procedure).replace(" ", "").lower()
    png_files = [f_name for f_name in os.listdir(IMAGE_DIR) if f_name.lower().endswith('.png')]

    # a) Suche nach patient_name UND procedure in Dateinamen
    for f_name in png_files:
        clean_f = f_name.replace(" ", "").lower()
        if clean_patient_name and clean_procedure and (clean_patient_name in clean_f) and (clean_procedure in clean_f):
            return os.path.join(IMAGE_DIR, f_name)

    # b) Wenn a nicht gefunden wurde, suche nur nach procedure
    for f_name in png_files:
        clean_f = f_name.replace(" ", "").lower()
        if clean_procedure and (clean_procedure in clean_f):
            return os.path.join(IMAGE_DIR, f_name)
    return None


def read_report_file(report_file):
    """Befundvorlage zuerst im Repo (reports/), sonst wie bisher in IMAGE_DIR suchen."""
    for base in (REPORTS_DIR, IMAGE_DIR):
        path = os.path.join(base, report_file)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    print(f"[!] Befundvorlage nicht gefunden: {report_file} (gesucht in {REPORTS_DIR} und {IMAGE_DIR})")
    return None


def build_report_text(study, patient_name, patient_id, accession_number, procedure):
    """
    Liefert (Befundtext, OpenMRS-Konzept).
    Reihenfolge: Fall-Befund aus cases.json ("report_text" oder Datei "report")
              -> unauffälliger Standardbefund aus default_reports.json
              -> REPORT_BOILERPLATE_TEMPLATE.
    Platzhalter wie {patient_name}, {procedure} oder {date} werden ersetzt.
    """
    template = None
    source = study or {}
    if study:
        template = study.get('report_text') or (read_report_file(study['report']) if study.get('report') else None)
    if template is None:
        default = find_default_report(procedure)
        if default:
            source = default
            template = default.get('report_text') or (read_report_file(default['report']) if default.get('report') else None)
            print(f"[*] Standardbefund '{default.get('name', '?')}' verwendet.")
    if template is None:
        template = REPORT_BOILERPLATE_TEMPLATE
    concept = source.get('concept') or REPORT_CONCEPT_NAME

    try:
        text = template.format(
            patient_name=patient_name if patient_name else "Unbekannt",
            patient_id=patient_id if patient_id else "-",
            accession_number=accession_number if accession_number else "-",
            procedure=procedure if procedure else "Radiologische Untersuchung",
            date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
    except (KeyError, IndexError, ValueError):
        # Vorlage enthält unbekannte/ungültige geschweifte Klammern -> unverändert verwenden
        text = template
    return text, concept


def create_png_dataset(template_file, png_path):
    """PNG in DICOM konvertieren (Pixeldaten und Dimensionen der Vorlage überschreiben)."""
    ds = dcmread(template_file)
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
    return ds


def create_image_dataset(image_path):
    """
    Erzeugt das Bild-DICOM je nach Dateityp:
    .mp4 -> Multi-Frame XA (Cine), .dcm -> fertiges DICOM übernehmen, sonst -> PNG/JPG über Vorlage.
    Patienten- und Studiendaten werden danach in process_json_trigger überschrieben.
    """
    ext = os.path.splitext(image_path)[1].lower()
    if ext == '.mp4':
        # Lazy Import: OpenCV wird nur benötigt, wenn tatsächlich ein Video verarbeitet wird
        from mp4_to_dicom import read_video_frames, create_video_dataset
        frames, fps = read_video_frames(image_path, max_width=VIDEO_MAX_WIDTH)
        print(f"[*] Video eingelesen: {len(frames)} Frames, {frames[0].shape[1]}x{frames[0].shape[0]} px, {fps:.2f} fps")
        return create_video_dataset(frames, fps, "", "", "", generate_uid(), "")
    if ext == '.dcm':
        return dcmread(image_path)
    return create_png_dataset(TEMPLATE_FILE, image_path)


def remove_trigger(file_path):
    """Trigger-Datei löschen, damit sie nicht doppelt verarbeitet wird."""
    if os.path.exists(file_path):
        os.remove(file_path)
    print("[*] Trigger-Datei bereinigt. Warte auf nächsten Auftrag...")


def publish_finding(ctx, report_text, concept, ward):
    """Befund als Text-Observation in OpenMRS ablegen (erscheint im Clinical Dashboard)."""
    if not (ctx.get("patient_uuid") and ctx.get("order_uuid")):
        print("[!] Patient/Order nicht in OpenMRS gefunden -> Befund wird nicht in OpenMRS gespeichert.")
        return
    try:
        publish_report_for_order(ctx["patient_uuid"], ctx["order_uuid"], report_text,
                                 concept_name=concept, location_name=ward)
    except Exception as rep_err:
        print(f"[X] Befund konnte nicht in OpenMRS gespeichert werden: {rep_err}")


def send_to_pacs(ds, report_ds):
    """Bild und Befund-Bild per C-STORE an dcm4chee senden. Gibt True zurück, wenn beides gespeichert wurde."""
    ae = AE(ae_title=PACS_AET)
    ae.add_requested_context(ds.file_meta.MediaStorageSOPClassUID)
    if hasattr(report_ds, 'file_meta') and report_ds.file_meta.MediaStorageSOPClassUID != ds.file_meta.MediaStorageSOPClassUID:
        ae.add_requested_context(report_ds.file_meta.MediaStorageSOPClassUID)

    print(f"[*] Sende Bild und Befundbericht an dcm4chee ({PACS_IP}:{PACS_PORT})...")
    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print(f"[X] FEHLER: Verbindung zu dcm4chee ({PACS_IP}:{PACS_PORT}) fehlgeschlagen.")
        if hasattr(assoc, 'is_rejected') and assoc.is_rejected:
            print(f"    Grund: DICOM Association wurde vom PACS abgewiesen (Result: {getattr(assoc, 'result', 'Rejected')}).")
        elif hasattr(assoc, 'is_aborted') and assoc.is_aborted:
            print("    Grund: DICOM Association wurde abgebrochen (Aborted).")
        else:
            print(f"    Grund: Kein TCP-Verbindungsaufbau zu {PACS_IP}:{PACS_PORT} möglich.")
        return False

    status_img = assoc.send_c_store(ds)
    img_success = hasattr(status_img, 'Status') and status_img.Status == 0x0000
    print(f"[{'V' if img_success else 'X'}] Bild übertragen (Status: {hex(status_img.Status) if hasattr(status_img, 'Status') else status_img})")

    status_rep = assoc.send_c_store(report_ds)
    rep_success = hasattr(status_rep, 'Status') and status_rep.Status == 0x0000
    print(f"[{'V' if rep_success else 'X'}] Befundbericht übertragen (Status: {hex(status_rep.Status) if hasattr(status_rep, 'Status') else status_rep})")

    assoc.release()
    # Hinweis: Früher stand hier (img_success or status_img) - das war immer wahr,
    # weil ein pydicom-Dataset als Objekt "truthy" ist. Jetzt zählt nur Status 0x0000.
    if img_success and rep_success:
        print("[V] ERFOLG: Bild und Befundbericht im PACS gespeichert!")
        return True
    print("[X] Übertragung ins PACS unvollständig.")
    return False


def process_json_trigger(file_path):
    # JSON-Daten von Mirth einlesen
    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"\n[+] Neuer Auftrag aus Bahmni erkannt!")
    patient_id = data.get('patient_id', '')
    patient_name = data.get('patient_name', '')
    accession_number = data.get('accession_number', '')
    procedure = data.get('procedure', '')
    dob = data.get('dob', '')
    ward = data.get('ward', '')

    # Geburtsdatum/Station + Patient-/Order-UUID aus OpenMRS nachladen
    # (UUIDs werden für den Befund in OpenMRS immer benötigt)
    ctx = {}
    try:
        ctx = lookup_patient_context(patient_id, accession_number)
        dob = dob or ctx["dob"]
        ward = ward or ctx["ward"]
    except Exception as lookup_err:
        print(f"[!] OpenMRS-Abfrage fehlgeschlagen ({lookup_err}) -> nur bisherige PNG-Suche, kein Befund in OpenMRS.")

    print(f"    Patienten-ID: {patient_id}")
    print(f"    Patienten-Name: {patient_name}")
    print(f"    Accession-Nr: {accession_number}")
    print(f"    Untersuchung: {procedure}")
    print(f"    Geburtsdatum: {dob}")
    print(f"    Station: {ward}")

    # Doppelte Aufträge überspringen: Gibt es für diese Order schon einen Befund in OpenMRS,
    # wurde sie bereits vollständig verarbeitet (Befund wird erst nach erfolgreichem PACS-Upload
    # geschrieben). Schützt vor doppelten Studien im PACS, wenn pacs-integration oder Mirth
    # dieselbe Order erneut schicken.
    if ctx.get("patient_uuid") and ctx.get("order_uuid"):
        try:
            if finding_exists_for_order(ctx["patient_uuid"], ctx["order_uuid"]):
                print(f"[i] Order {accession_number} wurde bereits verarbeitet (Befund vorhanden) -> übersprungen.")
                remove_trigger(file_path)
                return
        except Exception as dup_err:
            print(f"[!] Prüfung auf doppelte Order fehlgeschlagen ({dup_err}) -> verarbeite trotzdem.")

    # 1. Vorgefertigter Fall (Station + Geburtsdatum + Untersuchung) aus cases.json
    case, study = find_case_study(load_cases(CASES_FILE), ward, dob, procedure)
    if case:
        print(f"[+] Fall '{case.get('name', '?')}' erkannt.")

    # 2. Befundtext + Konzept (Fall-Befund oder unauffälliger Standardbefund)
    report_text, concept = build_report_text(study, patient_name, patient_id, accession_number, procedure)
    print(f"[*] Befund generiert für '{procedure}' ({patient_name}) -> Konzept '{concept}'")

    # 3. Bild suchen: Datei aus dem Fall, sonst bisherige PNG-Suche über den Dateinamen
    image_path = None
    if not os.path.exists(IMAGE_DIR):
        print(f"[X] FEHLER: Bildverzeichnis existiert nicht: {IMAGE_DIR}")
    elif study and study.get('file'):
        image_path = os.path.join(IMAGE_DIR, study['file'])
    else:
        image_path = find_legacy_png(patient_name, procedure)

    if not image_path or not os.path.exists(image_path):
        # Kein Bild (z. B. EKG) -> nur Befund in OpenMRS, nichts ins PACS
        print(f"[i] Kein Bild für Patient '{patient_name}' / Untersuchung '{procedure}' hinterlegt -> nur Befund in OpenMRS.")
        publish_finding(ctx, report_text, concept, ward)
        remove_trigger(file_path)
        return

    print(f"[+] Verwende Bilddatei: {image_path}")

    if not os.path.exists(TEMPLATE_FILE):
        print(f"[X] FEHLER: Die Bildvorlage fehlt unter: {TEMPLATE_FILE}")
        remove_trigger(file_path)
        return

    print(f"[*] Erzeuge Bild-DICOM und manipuliere DICOM-Header...")
    try:
        ds = create_image_dataset(image_path)
    except Exception as img_err:
        print(f"[X] FEHLER bei der Bild-Konvertierung: {img_err}")
        remove_trigger(file_path)
        return

    # GEMEINSAME StudyInstanceUID generieren:
    # Das ist das Herzstueck, damit Bild und Befund in derselben Studie in Oviyam2 erscheinen!
    shared_study_uid = generate_uid()

    # Bild-Metadaten mit den echten Bahmni-Werten überschreiben
    ds.PatientID = patient_id
    ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    ds.AccessionNumber = accession_number
    if dob:
        ds.PatientBirthDate = normalize_dob(dob)
    ds.StudyInstanceUID = shared_study_uid
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    if hasattr(ds, 'file_meta'):
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.StudyDescription = f"Radiology Order - {procedure}" if procedure else "Radiology Order"
    ds.SeriesDescription = (study or {}).get('description') or (f"Roentgen - {procedure}" if procedure else "Roentgenbild")
    ds.SpecificCharacterSet = "ISO_IR 192"
    # Befundtext auch direkt am Bild als ImageComment & StudyComment hinterlegen
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

    # 4. Ins PACS senden; Befund in OpenMRS nur, wenn die Bilder wirklich gespeichert wurden
    if send_to_pacs(ds, report_ds):
        publish_finding(ctx, report_text, concept, ward)
    else:
        print("[X] Befund wird nicht an OpenMRS gesendet, da die Bilder fehlen.")

    remove_trigger(file_path)

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
    # sudo ~/.venv/bahmni/bin/python KIS-Projekt/scripts/pacs_injector/pacs_injector.py
