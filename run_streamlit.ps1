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

# Set LLM API keys if not already set
if (-not $env:CHATLLM_API_KEY) {
    $env:CHATLLM_API_KEY = "s2_156073f76d354d72a6b0fb22c94a2f8d"
    Write-Host "[INFO] ChatLLM API key set from script" -ForegroundColor Green
} else {
    Write-Host "[INFO] ChatLLM API key already set" -ForegroundColor Yellow
}

if (-not $env:GROQ_API_KEY) {
    $env:GROQ_API_KEY = "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"
    Write-Host "[INFO] Groq API key set from script" -ForegroundColor Green
} else {
    Write-Host "[INFO] Groq API key already set" -ForegroundColor Yellow
}

# Set Supabase credentials if not already set
if (-not $env:SUPABASE_URL) {
    $env:SUPABASE_URL = "https://skfizxuvxenrltqdwkha.supabase.co"
    Write-Host "[INFO] Supabase URL set from script" -ForegroundColor Green
} else {
    Write-Host "[INFO] Supabase URL already set" -ForegroundColor Yellow
}

if (-not $env:SUPABASE_ANON_KEY) {
    $env:SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrZml6eHV2eGVucmx0cWR3a2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5NTM2OTksImV4cCI6MjA4MTUyOTY5OX0.33ovbBa5MqxXokTPn-RB4C9s7sFG4OaRfl3Zuz0fR6Y"
    Write-Host "[INFO] Supabase anon key set from script" -ForegroundColor Green
} else {
    Write-Host "[INFO] Supabase anon key already set" -ForegroundColor Yellow
}

# Check for Supabase credentials
if ($env:SUPABASE_URL -and $env:SUPABASE_ANON_KEY) {
    Write-Host "[INFO] Supabase credentials detected - using Supabase database" -ForegroundColor Green
}

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

