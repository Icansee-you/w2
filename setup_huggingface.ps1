# PowerShell script to set up Hugging Face API key
# Usage: .\setup_huggingface.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HUGGING FACE API SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if API key is already set
$existingKey = $env:HUGGINGFACE_API_KEY
if ($existingKey) {
    Write-Host "[INFO] HUGGINGFACE_API_KEY is already set: $($existingKey.Substring(0, [Math]::Min(8, $existingKey.Length)))..." -ForegroundColor Yellow
    Write-Host ""
    $useExisting = Read-Host "Do you want to use the existing key? (Y/n)"
    if ($useExisting -eq "n" -or $useExisting -eq "N") {
        $existingKey = $null
    }
}

if (-not $existingKey) {
    Write-Host "To get your Hugging Face API key:" -ForegroundColor Green
    Write-Host "1. Visit: https://huggingface.co/" -ForegroundColor White
    Write-Host "2. Sign up or log in (free account)" -ForegroundColor White
    Write-Host "3. Go to: Settings → Access Tokens" -ForegroundColor White
    Write-Host "4. Click 'New token'" -ForegroundColor White
    Write-Host "5. Select 'Read' permissions" -ForegroundColor White
    Write-Host "6. Copy your token (starts with 'hf_')" -ForegroundColor White
    Write-Host ""
    
    $apiKey = Read-Host "Enter your Hugging Face API token (or press Enter to skip)"
    
    if ($apiKey) {
        if (-not $apiKey.StartsWith("hf_")) {
            Write-Host "[WARNING] Token should start with 'hf_'. Continuing anyway..." -ForegroundColor Yellow
        }
        
        $env:HUGGINGFACE_API_KEY = $apiKey
        Write-Host ""
        Write-Host "[SUCCESS] API key set for this session!" -ForegroundColor Green
        Write-Host ""
        Write-Host "To make it permanent:" -ForegroundColor Yellow
        Write-Host "1. Create a .env file in the project root" -ForegroundColor White
        Write-Host "2. Add: HUGGINGFACE_API_KEY=$apiKey" -ForegroundColor White
        Write-Host ""
        
        # Offer to create .env file
        $createEnv = Read-Host "Do you want to create/update .env file now? (Y/n)"
        if ($createEnv -ne "n" -and $createEnv -ne "N") {
            if (Test-Path ".env") {
                # Check if HUGGINGFACE_API_KEY already exists
                $envContent = Get-Content ".env" -Raw
                if ($envContent -match "HUGGINGFACE_API_KEY=") {
                    $envContent = $envContent -replace "HUGGINGFACE_API_KEY=.*", "HUGGINGFACE_API_KEY=$apiKey"
                    Set-Content ".env" -Value $envContent -NoNewline
                    Write-Host "[SUCCESS] Updated .env file" -ForegroundColor Green
                } else {
                    Add-Content ".env" -Value "`nHUGGINGFACE_API_KEY=$apiKey"
                    Write-Host "[SUCCESS] Added to .env file" -ForegroundColor Green
                }
            } else {
                Set-Content ".env" -Value "HUGGINGFACE_API_KEY=$apiKey"
                Write-Host "[SUCCESS] Created .env file" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "[INFO] Skipped API key setup" -ForegroundColor Yellow
        Write-Host "You can set it later with: `$env:HUGGINGFACE_API_KEY='your_token'" -ForegroundColor White
    }
}

# Test the API key if set
if ($env:HUGGINGFACE_API_KEY) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TESTING HUGGING FACE API" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Note: Models may take 30-60 seconds to load on first use" -ForegroundColor Yellow
    Write-Host ""
    
    # Activate venv if it exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & "venv\Scripts\Activate.ps1"
    }
    
    Write-Host "Running test..." -ForegroundColor Yellow
    python test_huggingface.py
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  NEXT STEPS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "If the test passed:" -ForegroundColor Green
    Write-Host "1. Restart your Streamlit app" -ForegroundColor White
    Write-Host "2. The app will automatically use Hugging Face for:" -ForegroundColor White
    Write-Host "   - ELI5 summaries (child-friendly explanations)" -ForegroundColor White
    Write-Host "   - Article categorization" -ForegroundColor White
    Write-Host ""
    Write-Host "For Streamlit Cloud deployment:" -ForegroundColor Yellow
    Write-Host "1. Go to your app settings" -ForegroundColor White
    Write-Host "2. Add HUGGINGFACE_API_KEY to Secrets" -ForegroundColor White
    Write-Host ""
    Write-Host "Important notes:" -ForegroundColor Yellow
    Write-Host "- Models load on first use (30-60 seconds)" -ForegroundColor White
    Write-Host "- Free tier has rate limits" -ForegroundColor White
    Write-Host "- Some models work better for Dutch than others" -ForegroundColor White
    Write-Host ""
}

