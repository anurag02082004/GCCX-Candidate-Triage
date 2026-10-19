@echo off
start "GCCX Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
start "GCCX Frontend" cmd /k "cd /d %~dp0frontend && if not exist node_modules npm install && npm run dev"
