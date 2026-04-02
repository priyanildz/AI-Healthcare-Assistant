# Quick Start

## 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configure Environment
```bash
cp .env.example .env
```
Edit .env and set OPENAI_API_KEY.

## 3. Run Backend
```bash
cd backend
python app.py
```
Expected: http://127.0.0.1:5000

## 4. Run Angular Frontend
```bash
cd angular-frontend
npm install
npm start
```
Expected: http://localhost:4200 (or assigned port)

## 5. Health Check
```bash
curl http://localhost:5000/health
```

## Troubleshooting
- Port busy: stop process or use a different port.
- Missing module: reinstall dependencies.
- API errors in UI: check environment.prod.ts / backend URL.
