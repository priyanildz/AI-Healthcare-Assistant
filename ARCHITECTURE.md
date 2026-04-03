# Architecture

## Overview

Browser (Angular) --> Flask REST API --> AI/ML services + Database

## Frontend
- Angular application in angular-frontend/
- Feature pages: Home, X-Ray, Reports, Medications
- Theme support (light/dark)

## Backend
- Flask API in backend/app.py
- Model modules in backend/models/
- Stateless backend (no persistence layer)

## Data Flow
1. User submits input from Angular UI.
2. Angular calls Flask endpoints under /api/*.
3. Backend validates input and runs model logic.
4. Backend stores/returns analysis.
5. UI renders results.
