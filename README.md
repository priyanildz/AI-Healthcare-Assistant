# AI Healthcare Assistant

AI-powered healthcare project with:
- Flask backend API
- Angular frontend app
- Models for report summarization, medication review analysis, and X-ray analysis

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