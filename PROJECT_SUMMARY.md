# Project Summary

## Status
Core Flask + Angular implementation is active.
Legacy UI has been removed.

## Main Components
- backend/: Flask API, model integrations, database layer
- angular-frontend/: Angular 17 standalone frontend
- data/: sample or supporting data files

## Running
- Backend: cd backend && python app.py
- Frontend: cd angular-frontend && npm start

## Deployment Readiness
- Angular production build works.
- Vercel config exists in angular-frontend/vercel.json.
- Set correct production backend URL in angular-frontend/src/environments/environment.prod.ts.
