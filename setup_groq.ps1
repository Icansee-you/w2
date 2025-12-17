# PowerShell script to set up Groq API key
# Usage: .\setup_groq.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GROQ API SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if API key is already set
$existingKey = $env:GROQ_API_KEY
if ($existingKey) {
    Write-Host "[INFO] GROQ_API_KEY is already set: $($existingKey.Substring(0, [Math]::Min(8, $existingKey.Length)))..." -ForegroundColor Yellow
    Write-Host ""
    $useExisting = Read-Host "Do you want to use the existing key? (Y/n)"
    if ($useExisting -eq "n" -or $useExisting -eq "N") {
        $existingKey = $null
    }
}

if (-not $existingKey) {
    Write-Host "To get your Groq API key:" -ForegroundColor Green
    Write-Host "1. Visit: https://console.groq.com/" -ForegroundColor White
    Write-Host "2. Sign up or log in (free account)" -ForegroundColor White
    Write-Host "3. Go to API Keys section" -ForegroundColor White
    Write-Host "4. Click 'Create API Key'" -ForegroundColor White
    Write-Host ""
    
    $apiKey = Read-Host "Enter your Groq API key (or press Enter to skip)"
    
    if ($apiKey) {
        $env:GROQ_API_KEY = $apiKey
        Write-Host ""
        Write-Host "[SUCCESS] API key set for this session!" -ForegroundColor Green
        Write-Host ""
        Write-Host "To make it permanent:" -ForegroundColor Yellow
        Write-Host "1. Create a .env file in the project root" -ForegroundColor White
        Write-Host "2. Add: GROQ_API_KEY=$apiKey" -ForegroundColor White
        Write-Host ""
        
        # Offer to create .env file
        $createEnv = Read-Host "Do you want to create/update .env file now? (Y/n)"
        if ($createEnv -ne "n" -and $createEnv -ne "N") {
            if (Test-Path ".env") {
                # Check if GROQ_API_KEY already exists
                $envContent = Get-Content ".env" -Raw
                if ($envContent -match "GROQ_API_KEY=") {
                    $envContent = $envContent -replace "GROQ_API_KEY=.*", "GROQ_API_KEY=$apiKey"
                    Set-Content ".env" -Value $envContent -NoNewline
                    Write-Host "[SUCCESS] Updated .env file" -ForegroundColor Green
                } else {
                    Add-Content ".env" -Value "`nGROQ_API_KEY=$apiKey"
                    Write-Host "[SUCCESS] Added to .env file" -ForegroundColor Green
                }
            } else {
                Set-Content ".env" -Value "GROQ_API_KEY=$apiKey"
                Write-Host "[SUCCESS] Created .env file" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "[INFO] Skipped API key setup" -ForegroundColor Yellow
        Write-Host "You can set it later with: `$env:GROQ_API_KEY='your_key'" -ForegroundColor White
    }
}

# Test the API key if set
if ($env:GROQ_API_KEY) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TESTING GROQ API" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Activate venv if it exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & "venv\Scripts\Activate.ps1"
    }
    
    Write-Host "Running test..." -ForegroundColor Yellow
    python test_groq.py
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  NEXT STEPS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "If the test passed:" -ForegroundColor Green
    Write-Host "1. Restart your Streamlit app" -ForegroundColor White
    Write-Host "2. The app will automatically use Groq for:" -ForegroundColor White
    Write-Host "   - ELI5 summaries (child-friendly explanations)" -ForegroundColor White
    Write-Host "   - Article categorization" -ForegroundColor White
    Write-Host ""
    Write-Host "For Streamlit Cloud deployment:" -ForegroundColor Yellow
    Write-Host "1. Go to your app settings" -ForegroundColor White
    Write-Host "2. Add GROQ_API_KEY to Secrets" -ForegroundColor White
    Write-Host ""
}

