@echo off
echo ========================================
echo Barge Rate Forecasting Dashboard
echo ========================================
echo.
echo Starting Streamlit dashboard...
echo Dashboard will open in your default browser
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
streamlit run app.py

pause
