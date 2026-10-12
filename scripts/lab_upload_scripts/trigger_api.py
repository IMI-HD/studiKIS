from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

# Pfade auf dem HOST definieren
PYTHON_INTERPRETER = "/home/kislab/.venv/bahmni/bin/python3"
SCRIPT_PATH = "/home/kislab/KIS-Projekt/scripts/lab_upload_scripts/openelis_lab_simulator.py"

@app.route('/run-import', methods=['GET'])
def run_import():
    encounter_uuid = request.args.get('uuid')
    if not encounter_uuid:
        return jsonify({"error": "Missing uuid"}), 400
        
    try:
        # Führt das Skript nativ auf dem Host im venv aus
        result = subprocess.run(
            [PYTHON_INTERPRETER, SCRIPT_PATH, encounter_uuid],
            capture_output=True,
            text=True
        )
        return jsonify({
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Startet die API auf Port 5000 und lauscht auf allen IPs
    app.run(host='0.0.0.0', port=5000)