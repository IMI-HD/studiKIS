from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

import os
import sys

# Pfade auf dem HOST definieren (mit Fallback für lokale Tests)
PYTHON_INTERPRETER = "/home/kislab/.venv/bahmni/bin/python3"
if not os.path.exists(PYTHON_INTERPRETER):
    PYTHON_INTERPRETER = sys.executable

SCRIPT_PATH = "/home/kislab/KIS-Projekt/scripts/lab_upload_scripts/openelis_lab_simulator.py"
if not os.path.exists(SCRIPT_PATH):
    SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openelis_lab_simulator.py")

@app.route('/run-import', methods=['GET'])
def run_import():
    encounter_uuid = request.args.get('uuid')
    patient_id = request.args.get('patient_id') or request.args.get('patient')
    patient_uuid = request.args.get('patient_uuid')
    ward = request.args.get('ward') or request.args.get('location')
    dob = request.args.get('dob')
    
    if not encounter_uuid:
        return jsonify({"error": "Missing uuid"}), 400
        
    cmd = [PYTHON_INTERPRETER, SCRIPT_PATH, encounter_uuid]
    if patient_id:
        cmd.extend(["--patient-id", patient_id])
    if patient_uuid and patient_uuid != patient_id:
        cmd.extend(["--patient-uuid", patient_uuid])
    if ward:
        cmd.extend(["--ward", ward])
    if dob:
        cmd.extend(["--dob", dob])

    try:
        # Führt das Skript nativ auf dem Host im venv aus
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # WICHTIG: Ausgabe direkt an die Service-Konsole weiterleiten, damit journalctl sie erfasst
        if result.stdout:
            print(f"--- [LIS-Simulator Output: Encounter {encounter_uuid}] ---\n{result.stdout.strip()}", flush=True)
        if result.stderr:
            print(f"--- [LIS-Simulator Errors: Encounter {encounter_uuid}] ---\n{result.stderr.strip()}", file=sys.stderr, flush=True)

        return jsonify({
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }), 200
    except Exception as e:
        print(f"❌ Fehler bei Ausführung von openelis_lab_simulator.py: {e}", file=sys.stderr, flush=True)
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def view_logs():
    """
    Ermöglicht das bequeme Einsehen der Simulator-Logs direkt über den Browser oder curl.
    Beispiel: http://<server-ip>:5000/logs?lines=100
    """
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openelis_simulator.log")
    if not os.path.exists(log_file):
        return "Noch keine Simulator-Logdatei vorhanden. Wurde bereits ein Import ausgeführt?\n", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    try:
        lines_count = int(request.args.get('lines', 150))
    except ValueError:
        lines_count = 150
        
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            recent_lines = "".join(lines[-lines_count:])
            return recent_lines, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"Fehler beim Lesen der Logdatei: {e}\n", 500, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    # Startet die API auf Port 5000 und lauscht auf allen IPs
    app.run(host='0.0.0.0', port=5000)