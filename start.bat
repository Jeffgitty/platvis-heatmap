@echo off
echo Platvis Heatmap — lokale start
echo.

REM Backend starten in nieuwe terminal
start "Platvis Backend" cmd /k "cd backend && uvicorn main:app --reload --port 8000"

REM Even wachten zodat backend kan starten
timeout /t 2 /nobreak > nul

REM Frontend starten in nieuwe terminal
start "Platvis Frontend" cmd /k "cd frontend && npm run dev"

echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Sluit de twee vensters om te stoppen.
