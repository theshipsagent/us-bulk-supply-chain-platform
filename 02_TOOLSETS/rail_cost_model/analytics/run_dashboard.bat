@echo off
echo Starting Rail Analytics Dashboard...
cd /d "%~dp0"
streamlit run dashboards/app.py --server.port 8502
pause
