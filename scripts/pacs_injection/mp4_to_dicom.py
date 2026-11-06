import os
import argparse
from datetime import datetime

import cv2
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.encaps import encapsulate
from pydicom.tag import Tag
from pydicom.uid import generate_uid
from pynetdicom import AE


# 1. STANDARDPFADE
DEFAULT_VIDEO = "/home/kislab/dicom_images/Ventrikulografie mit mittelgradig reduzierter LVEF.mp4"

# X-Ray Angiographic Image Storage (Multi-Frame / Cine-fähig, passend für Ventrikulografie)
XA_IMAGE_STORAGE = "1.2.840.10008.5.1.4.1.1.12.1"

# JPEG Baseline: jeder Frame wird einzeln komprimiert, das Objekt bleibt ein normales Multi-Frame-Bild
JPEG_BASELINE_TRANSFER_SYNTAX = "1.2.840.10008.1.2.4.50"
DEFAULT_JPEG_QUALITY = 60


def read_video_frames(video_path, max_width=None, max_frames=None):
    """
    Liest alle Frames des Videos ein und wandelt sie in 8-Bit Graustufen um.
    Optional wird auf max_width herunterskaliert, um die DICOM-Datei weiter zu verkleinern.
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


def encode_frames_jpeg(frames, quality=DEFAULT_JPEG_QUALITY):
    """Komprimiert jeden Graustufen-Frame einzeln als JPEG Baseline und gibt die JPEG-Bytes zurück."""
    encoded = []
    for index, frame in enumerate(frames, start=1):
        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            raise ValueError(f"Frame {index} konnte nicht als JPEG kodiert werden")
        encoded.append(jpeg.tobytes())
    return encoded


def create_video_dataset(frames, fps, patient_id, patient_name, accession_number, study_instance_uid, description,
                         jpeg_quality=DEFAULT_JPEG_QUALITY):
    """
    Erstellt ein JPEG-komprimiertes Multi-Frame XA-DICOM (Cine-Loop) aus den Video-Frames.
    FrameTime + FrameIncrementPointer sorgen dafür, dass Viewer (z.B. Oviyam2) das Video abspielen.
    """
    sop_uid = generate_uid()

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = XA_IMAGE_STORAGE
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = JPEG_BASELINE_TRANSFER_SYNTAX

    ds = Dataset()
    ds.file_meta = file_meta
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")

    # Patient / Studie / Serie
    ds.SpecificCharacterSet = "ISO_IR 192"
    ds.SOPClassUID = XA_IMAGE_STORAGE
    ds.SOPInstanceUID = sop_uid
    ds.StudyInstanceUID = study_instance_uid
    ds.SeriesInstanceUID = generate_uid()
    ds.PatientID = patient_id
    ds.PatientName = patient_name if patient_name else "Patient^Bahmni"
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.AccessionNumber = accession_number
    ds.ReferringPhysicianName = ""
    ds.StudyID = "1"
    ds.StudyDate = date_str
    ds.StudyTime = time_str
    ds.SeriesDate = date_str
    ds.SeriesTime = time_str
    ds.ContentDate = date_str
    ds.ContentTime = time_str
    ds.AcquisitionDateTime = f"{date_str}{time_str}"
    ds.Modality = "XA"
    ds.Manufacturer = "KIS-Lab"
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.StudyDescription = description
    ds.SeriesDescription = description

    # XA-spezifische Attribute
    ds.ImageType = ["DERIVED", "SECONDARY", "SINGLE PLANE"]
    ds.PixelIntensityRelationship = "LIN"
    ds.RadiationSetting = "GR"
    ds.PositionerMotion = "STATIC"
    ds.KVP = ""
    ds.LossyImageCompression = "01"  # MP4-Quelle und JPEG-Frames sind verlustbehaftet komprimiert
    ds.LossyImageCompressionMethod = "ISO_10918_1"  # JPEG

    # Cine-Parameter
    frame_time_ms = 1000.0 / fps
    ds.NumberOfFrames = len(frames)
    ds.FrameTime = f"{frame_time_ms:.4f}"
    ds.FrameIncrementPointer = Tag(0x0018, 0x1063)  # zeigt auf FrameTime
    ds.CineRate = int(round(fps))
    ds.RecommendedDisplayFrameRate = int(round(fps))
    ds.StartTrim = 1
    ds.StopTrim = len(frames)

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

    # Gekapselte Pixeldaten: ein Fragment pro Frame, Padding auf gerade Länge übernimmt encapsulate()
    ds.PixelData = encapsulate(encode_frames_jpeg(frames, jpeg_quality))
    ds["PixelData"].VR = "OB"
    ds["PixelData"].is_undefined_length = True

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
    ae.add_requested_context(ds.file_meta.MediaStorageSOPClassUID, ds.file_meta.TransferSyntaxUID)

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
    parser = argparse.ArgumentParser(description="Wandelt eine MP4-Datei in ein Multi-Frame DICOM (XA Cine) um.")
    parser.add_argument("input", nargs="?", default=DEFAULT_VIDEO, help="Pfad zur MP4-Datei")
    parser.add_argument("-o", "--output", help="Ziel-DICOM (Standard: gleicher Name mit .dcm)")
    parser.add_argument("--max-width", type=int, default=1024, help="Maximale Bildbreite in Pixeln (0 = Original)")
    parser.add_argument("--max-frames", type=int, default=0, help="Maximale Anzahl Frames (0 = alle)")
    parser.add_argument("--jpeg-quality", type=int, default=DEFAULT_JPEG_QUALITY, help="JPEG-Qualität der Frames (1-100)")
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
    print(f"[+] {len(frames)} Frames, {cols}x{rows} px, {fps:.2f} fps")

    ds = create_video_dataset(
        frames=frames,
        fps=fps,
        patient_id=args.patient_id,
        patient_name=args.patient_name,
        accession_number=args.accession,
        study_instance_uid=generate_uid(),
        description=description,
        jpeg_quality=args.jpeg_quality
    )

    save_dataset(ds, output_path)
    print(f"[V] DICOM gespeichert: {output_path} ({os.path.getsize(output_path) / (1024 * 1024):.1f} MB)")

    if args.send:
        send_to_pacs(ds)


if __name__ == "__main__":
    main()
    # sudo ~/.venv/bahmni/bin/python KIS-Projekt/scripts/pacs_injection/mp4_to_dicom.py