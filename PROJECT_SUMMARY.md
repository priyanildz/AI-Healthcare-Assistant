# Project Summary

## Status
The project is set up for local development with a Flask backend and Angular frontend, with external AI APIs handling report, medication, and X-ray analysis.

## Main Components
- backend/: Flask API and model integrations
- angular-frontend/: Angular 17 standalone frontend

## Running
- Backend: `cd backend && python app.py`
- Frontend: `cd angular-frontend && npm install && npm start`

## Notes
- `data/` sample files were removed.
- `.env.example` is the source template for local environment variables.
- The backend expects requests from the Angular app running on `http://localhost:4200` during local development.
- X-ray analysis no longer depends on a local Torch model, which reduces deployment memory pressure on Render.