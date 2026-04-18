<div align="center">

# <img src="https://img.icons8.com/fluency/48/medical-doctor.png" width="40"/> AI Healthcare Assistant

### X-Ray Analysis • Medical NLP • Intelligent Healthcare System

<p>
A multi-module AI-powered healthcare assistant that combines computer vision and natural language processing to analyze medical data, assist diagnosis, and provide intelligent insights.
</p>

<br/>

<a href="YOUR_LIVE_LINK_HERE" target="_blank">
  <img src="https://img.shields.io/badge/Live%20Application-Open-1E88E5?style=for-the-badge&logo=google-chrome&logoColor=white" />
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Deep%20Learning-CNN-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white"/>
<img src="https://img.shields.io/badge/NLP-Text%20Analysis-8E24AA?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Flask-Web%20App-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/UI-Modern%20Dashboard-673AB7?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-2E7D32?style=for-the-badge"/>

</div>

---

## Overview

**AI Healthcare Assistant** is an advanced AI-driven system that integrates multiple healthcare functionalities into a single platform.

It combines:
- **Computer Vision** for X-ray analysis  
- **Natural Language Processing (NLP)** for medical reports  
- **Sentiment & semantic analysis** for medication reviews  

The application is designed with a strong focus on **safety, interpretability, and usability**, making it a comprehensive healthcare intelligence tool.

---

## Screenshots & Modules

<div align="center">

| Dashboard | Dark Mode |
|-----------|-----------|
| <img src="assets/home.png" width="400"/> | <img src="assets/dark.png" width="400"/> |

| Medical Reports | Medication Reviews |
|----------------|-------------------|
| <img src="assets/medical_reports.png" width="400"/> | <img src="assets/medication.png" width="400"/> |

| X-Ray Analysis |
|---------------|
| <img src="assets/xray.png" width="500"/> |

</div>

---

## Explanation of Features

### 1. Dashboard

- Central hub of the application  
- Provides access to all modules:
  - X-ray analysis  
  - Medical reports  
  - Medication reviews  
- Includes **dark/light mode toggle**  
- Designed for clean navigation and usability  

---

### 2. X-Ray Analysis (Computer Vision)

- Users upload chest X-ray images  
- Deep learning model analyzes the image  
- Outputs:
  - Predicted condition (Normal / Pneumonia / etc.)  
  - Confidence score  
  - Class probability distribution  
  - Clinical notes and recommendations  

This module uses **CNN-based image classification**.

---

### 3. Medical Reports (NLP)

- Users input medical report text  
- System processes and extracts key information  
- Outputs:
  - Categorized insights  
  - Structured summaries  
  - Important medical highlights  

This module uses **text processing and NLP techniques**.

---

### 4. Medication Reviews (NLP + Sentiment Analysis)

- Users input medication name and experience  
- System analyzes sentiment and extracts meaning  

Outputs include:
- Sentiment (positive/negative)  
- Confidence score  
- Therapeutic use  
- Summary  
- Key insights  

This helps understand real-world medication effectiveness.

---

### 5. Safety First Design

- If model confidence is low → avoids unreliable prediction  
- Encourages clinical review instead of blind automation  
- Designed to reduce risk in sensitive healthcare scenarios  

---

## Key Features

- Multi-module AI system (CV + NLP)  
- X-ray image classification  
- Medical text analysis and summarization  
- Sentiment analysis for medication reviews  
- Confidence-based safety mechanism  
- Modern responsive UI with dark mode  
- Structured and interpretable outputs  

---

## Technology Stack

<div align="center">

| Category | Technology |
|----------|-----------|
| Language | <img src="https://img.icons8.com/color/20/python.png"/> Python |
| Deep Learning | <img src="https://img.icons8.com/color/20/artificial-intelligence.png"/> TensorFlow / CNN |
| NLP | <img src="https://img.icons8.com/color/20/nlp.png"/> Text Processing |
| Backend | <img src="https://img.icons8.com/ios-filled/20/000000/flask.png"/> Flask |
| Frontend | <img src="https://img.icons8.com/color/20/html-5.png"/> HTML / CSS / JS |
| Visualization | <img src="https://img.icons8.com/color/20/combo-chart.png"/> Charts & UI Components |

</div>

---

## Project Structure

```
ai_healthcare_assistant/
├── app.py
├── models/
│   ├── xray_model.h5
│   └── nlp_models.pkl
├── routes/
│   ├── xray.py
│   ├── reports.py
│   └── medication.py
├── templates/
├── static/
├── assets/
│   ├── home.png
│   ├── dark.png
│   ├── medical_reports.png
│   ├── medication.png
│   └── xray.png
├── requirements.txt
└── README.md
```

---

## How It Works

1. User selects module  
2. Inputs data (image/text)  
3. Backend processes input using ML/DL models  
4. Results are generated with confidence scores  
5. Output is displayed with structured insights  

---

## Use Cases

- AI-assisted medical analysis  
- Educational healthcare tools  
- Clinical decision support (non-diagnostic)  
- Research and experimentation  

---

## Future Improvements

- Real-time deployment with APIs  
- Integration with hospital systems  
- Larger datasets for improved accuracy  
- Explainable AI visualizations  
- Mobile application support  

---

## Disclaimer

This application is for educational and research purposes only.  
It does not replace professional medical advice, diagnosis, or treatment.

---

## License

This project is licensed under the MIT License.

---

<div align="center">

Developed by  
<strong>priyanildz</strong>

</div>