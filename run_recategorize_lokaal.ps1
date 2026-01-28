# Hercategorisatie LLM-Failed lokaal (installeer deps indien nodig, voer script uit)
Set-Location $PSScriptRoot

Write-Host "Controleer dependencies..."
try {
    python -c "import supabase" 2>$null
} catch {}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installeren packages..."
    python -m pip install python-dotenv supabase groq requests pytz
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PIP install mislukt. Voer handmatig uit: pip install -r requirements.txt"
        exit 1
    }
}

Write-Host ""
Write-Host "Start hercategorisatie (1 artikel per 20 sec, eerst Groq dan RouteLLM)..."
python recategorize_llm_failed_only.py

Read-Host "Druk Enter om af te sluiten"
