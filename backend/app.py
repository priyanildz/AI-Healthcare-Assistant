"""Flask API for Healthcare AI Application"""
import uuid
from datetime import datetime
import inspect
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from config import config
from models.report_summarizer import ReportSummarizer
from models.medication_analyzer import MedicationAnalyzer
from models.xray_analyzer import XrayAnalyzer

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])
CORS(app)

# Initialize AI models
summarizer = ReportSummarizer()
med_analyzer = MedicationAnalyzer()
xray_analyzer = XrayAnalyzer()


def _enrich_summary_result(summary_result):
    """Backfill extended report fields for consistent frontend rendering."""
    abnormalities = summary_result.get("abnormalities", []) or []
    key_findings = summary_result.get("key_findings", []) or []
    recommendations = summary_result.get("recommendations", []) or []
    summary = summary_result.get("summary", "") or ""

    if "patient_friendly_explanation" not in summary_result:
        explanation_parts = []
        joined_findings = " ".join(str(x).lower() for x in key_findings)
        joined_abnormalities = " ".join(str(x).lower() for x in abnormalities)

        if "hemoglobin" in joined_findings or "rbc" in joined_findings or "anemia" in joined_abnormalities:
            explanation_parts.append(
                "Your blood report shows low hemoglobin or red blood cell levels, which may cause weakness or fatigue (anemia)."
            )
        if "wbc" in joined_findings or "infection" in joined_abnormalities:
            explanation_parts.append(
                "There is also an increased white blood cell pattern, which may indicate your body is fighting an infection."
            )
        summary_result["patient_friendly_explanation"] = " ".join(explanation_parts) or (
            "Please review these findings with your clinician for personalized medical advice."
        )

    if "severity_level" not in summary_result:
        level = "low"
        if abnormalities:
            level = "moderate"
        if len(abnormalities) >= 4:
            level = "high"
        summary_result["severity_level"] = level

    summary_result.setdefault("possible_causes", [
        "Iron deficiency anemia",
        "Recent or ongoing infection",
        "Inflammatory condition",
    ] if abnormalities else [])

    summary_result.setdefault("suggested_next_tests", [
        "Iron studies (Serum Ferritin)",
        "CRP / ESR (inflammation markers)",
        "Peripheral smear",
    ] if abnormalities else [])

    summary_result.setdefault("sections", {
        "summary": summary,
        "key_issues": abnormalities,
        "abnormal_values": key_findings,
        "recommendations": recommendations,
    })

    return summary_result

# ==================== HEALTH CHECK ====================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "report_summarizer": "ready",
            "medication_analyzer": "ready",
            "xray_analyzer": "ready"
        }
    })


@app.route('/debug/provider', methods=['GET'])
def debug_provider():
    """Debug endpoint to verify which provider and files are active at runtime."""
    local_src = inspect.getsource(getattr(summarizer, "_local_summarize", lambda: ""))
    return jsonify({
        "ai_provider_env": os.getenv("AI_PROVIDER", "<not-set>"),
        "report_provider": getattr(summarizer, "provider", "<missing>"),
        "med_provider": getattr(med_analyzer, "provider", "<missing>"),
        "report_file": inspect.getsourcefile(ReportSummarizer),
        "med_file": inspect.getsourcefile(MedicationAnalyzer),
        "debug_has_display_order": "display_order" in local_src,
        "debug_has_colon_scan": "for line in report_text.splitlines()" in local_src,
        "cwd": os.getcwd()
    })

# ==================== MEDICAL REPORTS ====================
@app.route('/api/reports/summarize', methods=['POST'])
def summarize_report():
    """Summarize a medical report"""
    try:
        data = request.json
        report_text = data.get('report_text', '')
        report_type = data.get('report_type', 'general')
        
        if not report_text:
            return jsonify({"error": "report_text is required"}), 400
        
        # Summarize using OpenAI
        summary_result = summarizer.summarize_report(report_text, report_type)
        summary_result = _enrich_summary_result(summary_result)
        
        if summary_result['status'] == 'success':
            return jsonify({
                "status": "success",
                "data": summary_result
            })
        else:
            return jsonify({
                "status": "error",
                "message": summary_result.get('message', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/summarize-file', methods=['POST'])
def summarize_report_file():
    """Summarize a medical report from uploaded image/PDF (Gemini mode)."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "file is required"}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({"error": "valid file is required"}), 400

        report_type = request.form.get('report_type', 'general')
        mime_type = file.mimetype or 'application/octet-stream'
        file_bytes = file.read()

        summary_result = summarizer.summarize_report_from_file(file_bytes, mime_type, report_type)
        summary_result = _enrich_summary_result(summary_result)

        if summary_result['status'] == 'success':
            return jsonify({
                "status": "success",
                "data": summary_result
            })

        return jsonify({
            "status": "error",
            "message": summary_result.get('message', 'Unknown error')
        }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== MEDICATION REVIEWS ====================
@app.route('/api/medications/analyze-review', methods=['POST'])
def analyze_medication_review():
    """Analyze a single medication review"""
    try:
        data = request.json
        review_text = data.get('review_text', '')
        medication_name = data.get('medication_name', '')
        
        if not review_text or not medication_name:
            return jsonify({"error": "review_text and medication_name are required"}), 400
        
        # Analyze review
        analysis = med_analyzer.analyze_review(review_text, medication_name)

        if analysis.get('status') == 'success' and not analysis.get('actual_use'):
            analysis['actual_use'] = med_analyzer._infer_actual_use(medication_name, review_text)
        
        if analysis['status'] == 'success':
            return jsonify({
                "status": "success",
                "data": analysis
            })
        else:
            return jsonify({
                "status": "error",
                "message": analysis.get('message', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/medications/aggregate-reviews', methods=['POST'])
def aggregate_medication_reviews():
    """Analyze multiple reviews for a medication"""
    try:
        data = request.json
        reviews = data.get('reviews', [])
        
        if not reviews:
            return jsonify({"error": "reviews array is required"}), 400
        
        # Aggregate analysis
        aggregated = med_analyzer.aggregate_reviews(reviews)
        
        return jsonify({
            "status": "success",
            "data": aggregated
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== X-RAY ANALYSIS ====================
@app.route('/api/xrays/analyze', methods=['POST'])
def analyze_xray():
    """Analyze an X-ray image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "image file is required"}), 400
        
        file = request.files['image']
        body_part = request.form.get('body_part', 'unknown')
        
        # Save temporary file
        temp_path = os.path.join(tempfile.gettempdir(), f"xray_{uuid.uuid4().hex[:8]}.jpg")
        file.save(temp_path)
        
        # Analyze X-ray
        analysis = xray_analyzer.analyze_xray(temp_path)
        
        if analysis['status'] == 'success':
            return jsonify({
                "status": "success",
                "data": analysis
            })
        else:
            return jsonify({
                "status": "error",
                "message": analysis.get('message', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
