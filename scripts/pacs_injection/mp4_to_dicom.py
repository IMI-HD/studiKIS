import os
import argparse

import cv2
from pydicom import dcmread
from pydicom.tag import Tag
from pydicom.uid import generate_uid
from pynetdicom import AE


# 1. STANDARDPFADE
DEFAULT_VIDEO = "/home/kislab/dicom_images/Ventrikulografie mit mittelgradig reduzierter LVEF.mp4"


def read_video_frames(video_path, max_width=None, max_frames=None):
    """
    Liest alle Frames des Videos ein und wandelt sie in 8-Bit Graustufen um.
    Optional wird auf max_width herunterskaliert, da unkomprimierte Multi-Frame-DICOMs
    sonst sehr groß werden (1080p x 300 Frames ≈ 600 MB).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Video konnte nicht geöffnet werden: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if max_width and gray.shape[1] > max_width:
            scale = max_width / gray.shape[1]
            new_size = (max_width, int(round(gray.shape[0] * scale)))
            gray = cv2.resize(gray, new_size, interpolation=cv2.INTER_AREA)
        frames.append(gray)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()

    if not frames:
        raise ValueError(f"Keine Frames im Video gefunden: {video_path}")
    # Manche Container liefern keine/unsinnige FPS -> sinnvoller Standardwert
    if fps <= 0 or fps > 1000:
        fps = 25.0
    return frames, fps


def create_video_dataset(frames, fps, patient_id, patient_name, accession_number, study_instance_uid, description,
                         template_file):
    """
    Erstellt aus den Video-Frames ein unkomprimiertes Multi-Frame-DICOM über die Bild-Vorlage.
    SOP-Klasse und Modalität kommen bewusst aus der Vorlage: Als XA gespeichert ließ sich das Video
    in Oviyam2 nicht durchblättern, mit der Vorlage funktioniert das auch bei gleicher Frame-Anzahl.
    """
    ds = dcmread(template_file)
    sop_uid = generate_uid()

    # Patient / Studie / Serie
    ds.SpecificCharacterSet = "ISO_IR 192"
    ds.SOPInstanceUID = sop_uid
    ds.file_meta.MediaStorageSOPInstanceUID = sop_uid
    ds.StudyInstanceUID = study_instance_uid
    ds.SeriesInstanceUID = generate_uid()
    ds.PatientID = patient_id
    ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    ds.AccessionNumber = accession_number
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.StudyDescription = description
    ds.SeriesDescription = description

    # Cine-Parameter
    ds.NumberOfFrames = len(frames)
    ds.FrameTime = f"{1000.0 / fps:.4f}"
    ds.FrameIncrementPointer = Tag(0x0018, 0x1063)  # zeigt auf FrameTime

    # Pixeldaten (8-Bit Graustufen)
    rows, cols = frames[0].shape
    ds.Rows = rows
    ds.Columns = cols
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    if 'PlanarConfiguration' in ds:
        del ds.PlanarConfiguration

    pixel_data = b"".join(f.tobytes() for f in frames)
    # PixelData muss gerade Byte-Länge haben (DICOM OB Padding)
    if len(pixel_data) % 2 != 0:
        pixel_data += b"\x00"
    ds.PixelData = pixel_data

    return ds


def save_dataset(ds, output_path):
    try:
        ds.save_as(output_path, enforce_file_format=True)  # pydicom >= 3
    except TypeError:
        ds.save_as(output_path, write_like_original=False)  # pydicom 2.x


def send_to_pacs(ds):
    # Lazy Import, da pacs_injector dieses Modul seinerseits importiert (kein Zirkelimport)
    from pacs_injector import PACS_IP, PACS_PORT, PACS_AET

    ae = AE(ae_title=PACS_AET)
    ae.add_requested_context(ds.file_meta.MediaStorageSOPClassUID)

    print(f"[*] Sende Video-DICOM an dcm4chee ({PACS_IP}:{PACS_PORT})...")
    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)
    if not assoc.is_established:
        print(f"[X] FEHLER: Verbindung zu dcm4chee ({PACS_IP}:{PACS_PORT}) fehlgeschlagen.")
        return False

    status = assoc.send_c_store(ds)
    assoc.release()
    success = hasattr(status, 'Status') and status.Status == 0x0000
    print(f"[{'V' if success else 'X'}] Video übertragen (Status: {hex(status.Status) if hasattr(status, 'Status') else status})")
    return success


def main():
    # Lazy Import, da pacs_injector dieses Modul seinerseits importiert (kein Zirkelimport)
    from pacs_injector import TEMPLATE_FILE

    parser = argparse.ArgumentParser(description="Wandelt eine MP4-Datei in ein Multi-Frame-DICOM um.")
    parser.add_argument("input", nargs="?", default=DEFAULT_VIDEO, help="Pfad zur MP4-Datei")
    parser.add_argument("-o", "--output", help="Ziel-DICOM (Standard: gleicher Name mit .dcm)")
    parser.add_argument("--template", default=TEMPLATE_FILE, help="DICOM-Vorlage")
    parser.add_argument("--max-width", type=int, default=1024, help="Maximale Bildbreite in Pixeln (0 = Original)")
    parser.add_argument("--max-frames", type=int, default=0, help="Maximale Anzahl Frames (0 = alle)")
    parser.add_argument("--patient-id", default="TEST001")
    parser.add_argument("--patient-name", default="Test^Patient")
    parser.add_argument("--accession", default="")
    parser.add_argument("--description", default=None, help="Studien-/Serienbeschreibung (Standard: Dateiname)")
    parser.add_argument("--send", action="store_true", help="Zusätzlich per C-STORE an dcm4chee senden")
    args = parser.parse_args()

    output_path = args.output or os.path.splitext(args.input)[0] + ".dcm"
    description = args.description or os.path.splitext(os.path.basename(args.input))[0]

    print(f"[*] Lese Video: {args.input}")
    frames, fps = read_video_frames(args.input, args.max_width or None, args.max_frames or None)
    rows, cols = frames[0].shape
    size_mb = rows * cols * len(frames) / (1024 * 1024)
    print(f"[+] {len(frames)} Frames, {cols}x{rows} px, {fps:.2f} fps (~{size_mb:.1f} MB Pixeldaten)")

    ds = create_video_dataset(
        frames=frames,
        fps=fps,
        patient_id=args.patient_id,
        patient_name=args.patient_name,
        accession_number=args.accession,
        study_instance_uid=generate_uid(),
        description=description,
        template_file=args.template
    )

    save_dataset(ds, output_path)
    print(f"[V] DICOM gespeichert: {output_path}")

    if args.send:
        send_to_pacs(ds)


if __name__ == "__main__":
    main()
    # sudo ~/.venv/bahmni/bin/python KIS-Projekt/scripts/pacs_injection/mp4_to_dicom.py
