@echo off
echo Gateway: 
curl -s http://localhost:8000/health
echo.
echo Account: 
curl -s http://localhost:8001/health
echo.
pause