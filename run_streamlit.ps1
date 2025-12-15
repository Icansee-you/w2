# PowerShell script to run Streamlit app
# This script activates the virtual environment and runs Streamlit

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Streamlit App" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Check if streamlit is installed
$streamlitCheck = python -m streamlit --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Streamlit not found in virtual environment!" -ForegroundColor Red
    Write-Host "Installing Streamlit..." -ForegroundColor Yellow
    pip install streamlit pytz python-dotenv
}

# Check if database exists or needs migration
if (-not (Test-Path "db.sqlite3")) {
    Write-Host "[INFO] Database not found. Running migrations..." -ForegroundColor Yellow
    python manage.py migrate --noinput
    python manage.py init_categories
}

Write-Host ""
Write-Host "Starting Streamlit..." -ForegroundColor Green
Write-Host "The app will open in your browser at http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run Streamlit
python -m streamlit run streamlit_app.py

