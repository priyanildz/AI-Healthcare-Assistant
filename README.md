# AI Healthcare Assistant

An AI-powered healthcare assistant that helps users analyze medical information, understand symptoms, and get intelligent insights using data-driven techniques.

---

## Live Demo

🔗 https://ai-healthcare-assistant-kokj.vercel.app/

---

## About the Project

AI Healthcare Assistant is a web-based application that uses AI and data analysis to help users:

- Understand health-related information  
- Analyze symptoms or medical data  
- Get meaningful insights using intelligent models  

It is designed to make healthcare information more accessible and easier to understand.


---

## Tech Stack

- Frontend: HTML, CSS, JavaScript  
- Backend: Python (Flask / API-based)  
- Deployment: Vercel  
- AI/ML: Data analysis / ML logic  

---

## How It Works

1. User inputs data (symptoms / query)  
2. Backend processes the input  
3. AI/Data logic analyzes it  
4. Results are displayed in simple format  

---

## Current Stack
- Backend: Flask stateless API using Gemini/Groq for analysis services
- Frontend: Angular 17 standalone app

## Deployment Notes
- X-ray analysis now uses an external vision API, which keeps the backend lightweight for Render.
- Use Render for the backend and Vercel for the frontend if you want separate deployments.

## Local Setup
1. Install backend dependencies with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and fill in the Gemini/Groq keys you need.
3. Start the backend with `cd backend && python app.py`.
4. Start the frontend with `cd angular-frontend && npm install && npm start`.

## Project Notes
- The project is organized as a two-part app: Angular UI plus Flask API.
- The sample `data/` folder has been removed because it is not required for runtime.
- API details are in `API_DOCUMENTATION.md`.
- Setup guidance is in `QUICKSTART.md`.