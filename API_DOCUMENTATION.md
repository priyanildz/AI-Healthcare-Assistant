"""
API Documentation and Usage Examples
"""

# Medical Report Analysis API
# ==========================

## Endpoint: POST /api/reports/summarize

### Description:
Analyze a medical report and generate summary, key findings, and recommendations

### Request:
```json
{
    "report_text": "Full medical report text here...",
    "report_type": "pathology|radiology|laboratory|clinical_notes",  // optional, default: "general"
    "patient_id": "P12345"  // optional
}
```

### Response (Success - 200):
```json
{
    "status": "success",
    "data": {
        "status": "success",
        "summary": "Concise summary of the report...",
        "key_findings": [
            "Finding 1",
            "Finding 2",
            "Finding 3"
        ],
        "abnormalities": [
            "Abnormality 1",
            "Abnormality 2"
        ],
        "recommendations": [
            "Recommendation 1",
            "Recommendation 2"
        ],
        "report_type": "pathology"
    },
    "database_id": "report_abc123xyz"
}
```

### Response (Error - 500):
```json
{
    "status": "error",
    "message": "Error message describing what went wrong"
}
```

### cURL Example:
```bash
curl -X POST http://localhost:5000/api/reports/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "report_text": "Patient presents with elevated WBC...",
    "report_type": "laboratory",
    "patient_id": "P001"
  }'
```

### Python Example:
```python
import requests

data = {
    "report_text": "Your medical report text...",
    "report_type": "pathology",
    "patient_id": "P12345"
}

response = requests.post(
    'http://localhost:5000/api/reports/summarize',
    json=data
)

print(response.json())
```

---

# Medication Review Analysis API
# ==============================

## Endpoint: POST /api/medications/analyze-review

### Description:
Analyze a single medication review for sentiment, side effects, and effectiveness

### Request:
```json
{
    "medication_name": "Aspirin",
    "review_text": "Great medication for headaches...",
    "patient_id": "P12345"  // optional
}
```

### Response (Success - 200):
```json
{
    "status": "success",
    "data": {
        "status": "success",
        "medication_name": "Aspirin",
        "sentiment_score": 0.85,  // -1 to 1
        "side_effects": [
            "Stomach upset",
            "Mild headache"
        ],
        "effectiveness_rating": 4.5,  // 0-5
        "impression": "Positive patient experience with medication...",
        "recommendation": "continue"
    },
    "database_id": "review_abc123xyz"
}
```

---

## Endpoint: POST /api/medications/aggregate-reviews

### Description:
Analyze multiple medication reviews and generate aggregate statistics

### Request:
```json
{
    "reviews": [
        {
            "medication_name": "Aspirin",
            "text": "Great for pain relief..."
        },
        {
            "medication_name": "Aspirin",
            "text": "Caused stomach issues..."
        }
    ]
}
```

### Response (Success - 200):
```json
{
    "status": "success",
    "data": {
        "total_reviews_analyzed": 2,
        "average_sentiment": 0.42,
        "average_effectiveness": 4.0,
        "most_common_side_effects": [
            ["Stomach upset", 1],
            ["Nausea", 1]
        ],
        "sentiment_distribution": {
            "positive": 1,
            "neutral": 0,
            "negative": 1
        },
        "detailed_analyses": [ /* ... */ ]
    }
}
```

---

# X-Ray Analysis API
# ==================

## Endpoint: POST /api/xrays/analyze

### Description:
Analyze an X-ray image for abnormalities and classification

### Request:
```
Content-Type: multipart/form-data

Parameters:
- image (file): X-ray image file (jpg, png, bmp)
- patient_id (string, optional): Patient identifier
- body_part (string, optional): Body part analyzed (chest, arm, leg, etc.)
```

### Response (Success - 200):
```json
{
    "status": "success",
    "data": {
        "status": "success",
        "image_path": "/tmp/xray_xyz.jpg",
        "classification": "Normal",  // Normal, Pneumonia, COVID-19, TB, Abnormal
        "confidence_score": 0.95,
        "findings": "No significant abnormalities detected...",
        "all_probabilities": {
            "Normal": 0.95,
            "Pneumonia": 0.03,
            "COVID-19": 0.01,
            "Tuberculosis": 0.01,
            "Abnormal": 0.00
        }
    },
    "database_id": "xray_abc123xyz"
}
```

### cURL Example:
```bash
curl -X POST http://localhost:5000/api/xrays/analyze \
  -F "image=@/path/to/xray.jpg" \
  -F "patient_id=P001" \
  -F "body_part=chest"
```

### Python Example:
```python
import requests

with open('xray.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'patient_id': 'P001',
        'body_part': 'chest'
    }
    response = requests.post(
        'http://localhost:5000/api/xrays/analyze',
        files=files,
        data=data
    )

print(response.json())
```

---

# Retrieve Results API
# ====================

## Endpoint: GET /api/reports/<report_id>

### Description:
Retrieve a previously analyzed medical report

### Response (Success - 200):
```json
{
    "id": "report_abc123xyz",
    "original_text": "Full original report...",
    "summary": "Summary...",
    "key_findings": [...],
    "report_type": "pathology",
    "patient_id": "P001",
    "created_at": "2024-03-21T10:30:00"
}
```

---

## Endpoint: GET /api/xrays/<xray_id>

### Description:
Retrieve previously analyzed X-ray results

### Response (Success - 200):
```json
{
    "id": "xray_abc123xyz",
    "classification": "Normal",
    "confidence_score": 0.95,
    "findings": "...",
    "body_part": "chest",
    "patient_id": "P001",
    "created_at": "2024-03-21T10:30:00"
}
```

---

# System Health Check API
# =======================

## Endpoint: GET /health

### Description:
Check if the API and all services are running

### Response (Success - 200):
```json
{
    "status": "healthy",
    "timestamp": "2024-03-21T10:30:00",
    "services": {
        "database": "connected",
        "report_summarizer": "ready",
        "medication_analyzer": "ready",
        "xray_analyzer": "ready"
    }
}
```

---

# HTTP Status Codes
# =================

- 200 OK: Request successful
- 400 Bad Request: Invalid input parameters
- 401 Unauthorized: Authentication required (future feature)
- 404 Not Found: Resource not found
- 500 Internal Server Error: Server error during processing
- 503 Service Unavailable: Service temporarily unavailable

---

# Error Handling
# ==============

All error responses follow this format:

```json
{
    "status": "error",
    "message": "Human-readable error message"
}
```

Common errors:
- Missing required fields
- Invalid file format (for X-ray)
- API rate limit exceeded
- OpenAI API failure
- Database connection error

---

# Rate Limiting (Future)
# ======================

Current: No rate limiting
Future: 
- 100 requests per minute per IP
- 1000 requests per hour per API key
- Rate limit headers in response

---

# Authentication (Future)
# =======================

Will use JWT tokens:

```
Authorization: Bearer <jwt_token>
```
