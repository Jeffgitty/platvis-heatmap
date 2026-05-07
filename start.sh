#!/bin/bash
# Platvis Heatmap — lokale start (Mac/Linux)

echo "Backend starten op http://localhost:8000 ..."
(cd backend && uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

echo "Frontend starten op http://localhost:5173 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Druk Ctrl+C om alles te stoppen."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
