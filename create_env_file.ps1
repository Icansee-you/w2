# Script to create .env file with Supabase credentials
# Run this: .\create_env_file.ps1

$envContent = @"
# Supabase Configuration
SUPABASE_URL=https://skfizxuvxenrltqdwkha.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrZml6eHV2eGVucmx0cWR3a2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5NTM2OTksImV4cCI6MjA4MTUyOTY5OX0.33ovbBa5MqxXokTPn-RB4C9s7sFG4OaRfl3Zuz0fR6Y

# LLM API Keys
GROQ_API_KEY=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
CHATLLM_API_KEY=s2_156073f76d354d72a6b0fb22c94a2f8d
"@

if (Test-Path ".env") {
    Write-Host ".env file already exists. Updating..." -ForegroundColor Yellow
    Set-Content ".env" -Value $envContent
    Write-Host "[OK] .env file updated!" -ForegroundColor Green
} else {
    Set-Content ".env" -Value $envContent
    Write-Host "[OK] .env file created!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next step: Set up database tables in Supabase" -ForegroundColor Yellow
Write-Host "  1. Go to: https://supabase.com/dashboard/project/skfizxuvxenrltqdwkha" -ForegroundColor White
Write-Host "  2. Click 'SQL Editor' → 'New query'" -ForegroundColor White
Write-Host "  3. Copy contents of 'supabase_schema.sql' and run it" -ForegroundColor White

