# API Documentation

Base URL for local development: `http://127.0.0.1:5000`

This backend uses Gemini/Groq for report and medication analysis, and an external vision API for X-ray analysis.

## Health Check

### `GET /health`
Returns the service status and loaded components.

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-03T12:00:00.000000",
  "services": {
    "report_summarizer": "ready",
    "medication_analyzer": "ready",
    "xray_analyzer": "ready"
  }
}
```

## Provider Debug

### `GET /debug/provider`
Returns runtime provider details for local troubleshooting.

Example response:
```json
{
  "ai_provider_env": "local",
  "report_provider": "local",
  "med_provider": "local",
  "report_file": "backend/models/report_summarizer.py",
  "med_file": "backend/models/medication_analyzer.py",
  "debug_has_display_order": true,
  "debug_has_colon_scan": true,
  "cwd": "D:\\02 Course\\01 Project\\AI_Healthcare_Project\\backend"
}
```

## Medical Report Analysis

### `POST /api/reports/summarize`
Analyzes pasted report text.

Request body:
```json
{
  "report_text": "Patient has elevated WBC...",
  "report_type": "laboratory"
}
```

Success response:
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "summary": "...",
    "key_findings": ["..."],
    "abnormalities": ["..."],
    "recommendations": ["..."],
    "patient_friendly_explanation": "...",
    "severity_level": "low",
    "possible_causes": [],
    "suggested_next_tests": [],
    "sections": {
      "summary": "...",
      "key_issues": [],
      "abnormal_values": [],
      "recommendations": []
    },
    "report_type": "laboratory"
  }
}
```

### `POST /api/reports/summarize-file`
Analyzes an uploaded image or PDF report when file-based input is needed.

Form data:
- `file` required
- `report_type` optional

## Medication Review Analysis

### `POST /api/medications/analyze-review`
Analyzes a single medication review.

Request body:
```json
{
  "medication_name": "Amlodipine",
  "review_text": "This helped control my blood pressure..."
}
```

Success response:
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "medication_name": "Amlodipine",
    "actual_use": "Treats high blood pressure (hypertension).",
    "sentiment_score": 0.8,
    "sentiment": "positive",
    "side_effects": [],
    "effectiveness_rating": 4.5,
    "impression": "...",
    "review_summary": "...",
    "key_points": ["..."],
    "confidence": 0.9,
    "recommendation": "continue"
  }
}
```

### `POST /api/medications/aggregate-reviews`
Analyzes multiple reviews for one medication.

Request body:
```json
{
  "reviews": [
    {
      "medication_name": "Amlodipine",
      "text": "Worked well for my BP"
    }
  ]
}
```

## X-Ray Analysis

### `POST /api/xrays/analyze`
Analyzes an uploaded X-ray image using an external vision provider.

Form data:
- `image` required
- `body_part` optional

Success response:
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "image_path": "/tmp/xray_1234.jpg",
    "classification": "Normal",
    "confidence_score": 0.95,
    "confidence": 0.95,
    "findings": "...",
    "finding": "...",
    "clinical_note": "...",
    "recommendations": ["..."],
    "all_probabilities": {
      "Normal": 0.95
    },
    "probabilities": {
      "Normal": 0.95
    }
  }
}
```

The probability values are model estimates returned by the vision provider and are intended for UI display, not clinical decision-making.

## Error Responses

Validation errors return HTTP 400 with a JSON body like:
```json
{ "error": "report_text is required" }
```

Unexpected errors return HTTP 500 with a JSON body like:
```json
{ "error": "Internal server error" }
```