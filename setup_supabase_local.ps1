# PowerShell script to set up Supabase for local development
# Usage: .\setup_supabase_local.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Supabase Local Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Your Supabase project URL (extracted from connection string)
$supabaseUrl = "https://skfizxuvxenrltqdwkha.supabase.co"

Write-Host "Your Supabase Project:" -ForegroundColor Green
Write-Host "  URL: $supabaseUrl" -ForegroundColor White
Write-Host ""

Write-Host "Step 1: Get your Supabase Anon Key" -ForegroundColor Yellow
Write-Host "  1. Go to: https://supabase.com/dashboard" -ForegroundColor White
Write-Host "  2. Select your project" -ForegroundColor White
Write-Host "  3. Go to: Project Settings → API" -ForegroundColor White
Write-Host "  4. Copy the 'anon/public' key (long string starting with 'eyJ...')" -ForegroundColor White
Write-Host ""

$anonKey = Read-Host "Enter your Supabase anon key (or press Enter to skip)"

if ($anonKey) {
    Write-Host ""
    Write-Host "Step 2: Creating .env file..." -ForegroundColor Yellow
    
    # Create .env file content
    $envContent = @"
# Supabase Configuration
SUPABASE_URL=$supabaseUrl
SUPABASE_ANON_KEY=$anonKey

# LLM API Keys
GROQ_API_KEY=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
CHATLLM_API_KEY=s2_156073f76d354d72a6b0fb22c94a2f8d
"@
    
    # Check if .env exists
    if (Test-Path ".env") {
        $overwrite = Read-Host ".env file already exists. Overwrite? (y/n)"
        if ($overwrite -eq "y" -or $overwrite -eq "Y") {
            Set-Content ".env" -Value $envContent
            Write-Host "✅ .env file updated!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Keeping existing .env file" -ForegroundColor Yellow
        }
    } else {
        Set-Content ".env" -Value $envContent
        Write-Host "✅ .env file created!" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Step 3: Set up database tables" -ForegroundColor Yellow
    Write-Host "  1. Go to: https://supabase.com/dashboard/project/skfizxuvxenrltqdwkha" -ForegroundColor White
    Write-Host "  2. Click 'SQL Editor' in the left sidebar" -ForegroundColor White
    Write-Host "  3. Click 'New query'" -ForegroundColor White
    Write-Host "  4. Open 'supabase_schema.sql' from this project" -ForegroundColor White
    Write-Host "  5. Copy ALL the SQL code and paste it into the SQL Editor" -ForegroundColor White
    Write-Host "  6. Click 'Run' (or press Ctrl+Enter)" -ForegroundColor White
    Write-Host ""
    Write-Host "  7. Verify tables were created:" -ForegroundColor White
    Write-Host "     - Go to 'Table Editor' in left sidebar" -ForegroundColor White
    Write-Host "     - You should see 'articles' and 'user_preferences' tables" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Step 4: Test the connection" -ForegroundColor Yellow
    Write-Host "  Run: .\run_streamlit.ps1" -ForegroundColor White
    Write-Host "  Look for: '[INFO] Supabase credentials detected - using Supabase database'" -ForegroundColor White
    Write-Host ""
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Set up database tables (see Step 3 above)" -ForegroundColor White
    Write-Host "  2. Run the app: .\run_streamlit.ps1" -ForegroundColor White
    Write-Host "  3. Test by signing up and importing articles" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  Setup skipped. You can run this script again later." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set up manually:" -ForegroundColor Yellow
    Write-Host "  1. Create .env file with:" -ForegroundColor White
    Write-Host "     SUPABASE_URL=$supabaseUrl" -ForegroundColor Cyan
    Write-Host "     SUPABASE_ANON_KEY=your-anon-key-here" -ForegroundColor Cyan
    Write-Host "  2. Get anon key from: Project Settings → API" -ForegroundColor White
    Write-Host "  3. Run supabase_schema.sql in Supabase SQL Editor" -ForegroundColor White
}

