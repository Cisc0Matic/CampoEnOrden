# CampoEnOrden - Iniciar backend y frontend

$ErrorActionPreference = "Stop"

Write-Host "Iniciando backend Django..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend\campoenorden_backend; .\venv\Scripts\activate; python manage.py runserver 0.0.0.0:8000"

Start-Sleep -Seconds 3

Write-Host "Iniciando frontend Ionic..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend\campoenorden_frontend; npx ionic serve --host 0.0.0.0 --port 8100"

Write-Host "Servidores iniciados:" -ForegroundColor Yellow
Write-Host "  Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:8100" -ForegroundColor Cyan
