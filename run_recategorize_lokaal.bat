@echo off
REM Draai hercategorisatie LLM-Failed lokaal (met venv/deps).
cd /d "%~dp0"

echo Controleer dependencies...
python -c "import supabase" 2>nul || (
  echo Installeren packages...
  pip install python-dotenv supabase groq requests pytz
  if errorlevel 1 (
    echo PIP install mislukt. Voer handmatig uit: pip install -r requirements.txt
    pause
    exit /b 1
  )
)

echo.
echo Start hercategorisatie (1 artikel per 20 sec, eerst Groq dan RouteLLM)...
python recategorize_llm_failed_only.py

pause
