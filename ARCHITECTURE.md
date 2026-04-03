# Architecture

## Overview

Angular frontend -> Flask REST API -> AI model services

## Frontend
- Angular application in `angular-frontend/`
- Feature pages: Home, X-Ray, Reports, Medications
- Theme support: light and dark mode

## Backend
- Flask API in `backend/app.py`
- Model modules in `backend/models/`
- Stateless backend, no database or persistence layer

## Data Flow
1. User enters report text, review text, or an image in the Angular UI.
2. Angular sends requests to Flask under `/api/*`.
3. Flask validates input and calls the model services.
4. The API returns analysis results as JSON.
5. The UI renders the returned analysis.