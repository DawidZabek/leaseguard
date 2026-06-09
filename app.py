import os
import sys
import json
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from rag.setup import setup_rag
from agents.extractor import run_extractor
from agents.advisor import run_advisor
from agents.photo import run_photo_analysis
from agents.protocol import run_protocol

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "leaseguard-dev-secret")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contract")
def contract_page():
    return render_template("contract.html")


@app.route("/protocol")
def protocol_page():
    return render_template("protocol.html")


@app.route("/api/analyze-contract", methods=["POST"])
def analyze_contract():
    data = request.get_json()
    if not data or not data.get("contract_text"):
        return jsonify({"error": "Brak tekstu umowy"}), 400

    contract_text = data["contract_text"].strip()
    if len(contract_text) < 100:
        return jsonify({"error": "Tekst umowy jest zbyt krótki"}), 400

    try:
        clauses, clause_risks = run_extractor(contract_text)
        if not clauses:
            return jsonify({"error": "Nie wykryto żadnych klauzul w tekście"}), 400

        report = run_advisor(clause_risks)

        return jsonify({
            "clauses": [
                {
                    "clause_type": cr.clause.clause_type,
                    "content": cr.clause.content,
                    "raw_excerpt": cr.clause.raw_excerpt,
                    "article_reference": cr.clause.article_reference,
                    "status": cr.status,
                    "justification": cr.justification,
                    "legal_basis": cr.legal_basis,
                    "recommendation": cr.recommendation,
                }
                for cr in report.clauses
            ],
            "questions_for_landlord": report.questions_for_landlord,
            "overall_recommendation": report.overall_recommendation,
            "risk_summary": report.risk_summary,
        })
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Błąd parsowania odpowiedzi AI: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Błąd analizy: {str(e)}"}), 500


@app.route("/api/analyze-photos", methods=["POST"])
def analyze_photos():
    if "photos" not in request.files:
        return jsonify({"error": "Brak zdjęć"}), 400

    files = request.files.getlist("photos")
    address = request.form.get("address", "")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Nie wybrano żadnych plików"}), 400

    saved_paths = []
    try:
        for file in files:
            if file and allowed_file(file.filename):
                filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(path)
                saved_paths.append(path)

        if not saved_paths:
            return jsonify({"error": "Żaden z przesłanych plików nie jest obsługiwanym formatem obrazu"}), 400

        rooms = [run_photo_analysis(path) for path in saved_paths]
        protocol = run_protocol(rooms, address)

        return jsonify({
            "rooms": [
                {
                    "room_name": r.room_name,
                    "defects": r.defects,
                    "general_condition": r.general_condition,
                    "recommendations": r.recommendations,
                    "photo_description": r.photo_description,
                }
                for r in protocol.rooms
            ],
            "protocol_text": protocol.protocol_text,
            "total_defects": protocol.total_defects,
            "property_address": protocol.property_address,
        })
    except Exception as e:
        return jsonify({"error": f"Błąd analizy zdjęć: {str(e)}"}), 500
    finally:
        for path in saved_paths:
            try:
                os.remove(path)
            except OSError:
                pass


if __name__ == "__main__":
    print("Inicjalizacja bazy RAG...")
    setup_rag()
    print("LeaseGuard uruchomiony na http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
