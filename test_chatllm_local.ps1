# PowerShell script to test ChatLLM locally
# This sets the environment variable and runs the Streamlit app

Write-Host "Setting up ChatLLM API key for local testing..." -ForegroundColor Green

# Set the ChatLLM API key
$env:CHATLLM_API_KEY = "s2_733cff6da442497eb4f1a5f2e11f9d7a"

Write-Host "✓ ChatLLM API key set" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Streamlit app..." -ForegroundColor Green
Write-Host "The app will open in your browser automatically." -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & "venv\Scripts\Activate.ps1"
}

# Run Streamlit
streamlit run streamlit_app.py


