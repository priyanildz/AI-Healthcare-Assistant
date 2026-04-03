# Quick Start

## 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configure Environment
```bash
copy .env.example .env
```
Edit `.env` and set the Gemini and Groq API keys you want to use.

## 3. Run Backend
```bash
cd backend
python app.py
```
Expected: `http://127.0.0.1:5000`

## 4. Run Angular Frontend
```bash
cd angular-frontend
npm install
npm start
```
Expected: `http://localhost:4200` (or the port shown by Angular)

## 5. Health Check
```bash
curl http://localhost:5000/health
```

## Troubleshooting
- Port busy: stop the process already using the port and start again.
- Missing Python package: reinstall with `pip install -r requirements.txt`.
- Frontend API errors: confirm the backend is running and the API base URL points to `http://127.0.0.1:5000/api`.
- Render OOM: verify you are using the external X-ray vision flow and not a local Torch model.