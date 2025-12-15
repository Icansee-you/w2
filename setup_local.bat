@echo off
REM Setup script for Windows to prepare local Streamlit environment

echo ============================================================
echo Streamlit Local Setup
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================================
echo Setup complete!
echo.
echo Next steps:
echo 1. Make sure virtual environment is activated (you should see (venv) in prompt)
echo 2. Run: python manage.py migrate
echo 3. Run: python manage.py init_categories
echo 4. Run: streamlit run streamlit_app.py
echo ============================================================

pause

