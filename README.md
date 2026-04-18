<div align="center">

# <img src="https://img.icons8.com/fluency/48/medical-doctor.png" width="40"/> AI Healthcare Project

### Disease Prediction • Machine Learning • Healthcare Analytics

<p>
An AI-powered healthcare application that predicts possible diseases based on user-input symptoms using machine learning techniques.
</p>

<br/>

<a href="YOUR_LIVE_LINK_HERE" target="_blank">
  <img src="https://img.shields.io/badge/Live%20Application-Open-1E88E5?style=for-the-badge&logo=google-chrome&logoColor=white" />
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Machine%20Learning-Model-FF6F00?style=for-the-badge&logo=scikitlearn&logoColor=white"/>
<img src="https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas&logoColor=white"/>
<img src="https://img.shields.io/badge/NumPy-Numerical-013243?style=for-the-badge&logo=numpy&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-Web%20App-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-2E7D32?style=for-the-badge"/>

</div>

---

## Overview

**AI Healthcare Project** is a machine learning-based system designed to predict potential diseases based on user-provided symptoms.

The application analyzes symptom patterns and maps them to likely diseases using trained models, helping users gain preliminary insights into possible health conditions.

---

## Screenshots

<div align="center">

| Symptom Input | Prediction Result |
|---------------|------------------|
| <img src="assets/input.png" width="400"/> | <img src="assets/output.png" width="400"/> |

</div>

---

## Explanation of UI & Prediction

### 1. Symptom Input Screen

- Users enter symptoms through a form interface  
- Inputs are processed and converted into numerical features  
- These features are passed to the trained model  

---

### 2. Prediction Output Screen

- Displays the predicted disease based on input symptoms  
- Shows the most likely condition derived from the model  
- May include additional information such as confidence or related symptoms  

This represents the **final prediction output of the ML model**.

---

## Key Features

- Disease prediction using machine learning  
- Symptom-based input system  
- Real-time prediction output  
- Data preprocessing and feature mapping  
- Web-based interface using Flask  
- Easy-to-use and responsive design  

---

## Technology Stack

<div align="center">

| Category | Technology |
|----------|-----------|
| Language | <img src="https://img.icons8.com/color/20/python.png"/> Python |
| ML Framework | <img src="https://img.icons8.com/color/20/artificial-intelligence.png"/> Scikit-learn |
| Data Processing | <img src="https://img.icons8.com/color/20/pandas.png"/> Pandas |
| Numerical | <img src="https://img.icons8.com/color/20/numpy.png"/> NumPy |
| Backend | <img src="https://img.icons8.com/ios-filled/20/000000/flask.png"/> Flask |
| Frontend | <img src="https://img.icons8.com/color/20/html-5.png"/> HTML |

</div>

---

## Project Structure

```
02_ai_healthcare/
├── dataset/
│   └── disease_data.csv
├── model/
│   └── trained_model.pkl
├── app.py
├── templates/
│   ├── index.html
│   └── result.html
├── static/
│   └── style.css
├── requirements.txt
└── assets/
    ├── input.png
    └── output.png
```

---

## How It Works

1. User inputs symptoms  
2. Input is preprocessed into model-readable format  
3. Model analyzes symptom patterns  
4. Prediction is generated  
5. Result is displayed on UI  

---

## Model Details

- Classification model trained on symptom-disease dataset  
- Learns relationships between symptoms and diseases  
- Outputs most probable disease  

---

## Getting Started

### Prerequisites

- Python 3.8+  

---

### Installation

```bash
git clone https://github.com/priyanildz/AI-Healthcare-Project.git
cd AI-Healthcare-Project
```

```bash
python -m venv venv
```

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## Use Cases

- Preliminary disease prediction  
- Healthcare data analysis  
- Educational ML project  
- Decision-support systems  

---

## Future Improvements

- Add more diseases and datasets  
- Improve model accuracy  
- Add confidence scores  
- Deploy as full-scale healthcare assistant  
- Integrate with medical APIs  

---

## Disclaimer

This project is for educational purposes only and should not be used as a substitute for professional medical advice.

---

## License

This project is licensed under the MIT License.

---

<div align="center">

Developed by  
<strong>priyanildz</strong>

</div>