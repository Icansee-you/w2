# PowerShell script to push code to GitHub
# Repository: https://github.com/Icansee-you/test1830

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Pushing to GitHub: Icansee-you/test1830" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "[OK] Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Git is not installed or not in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Or use GitHub Desktop: https://desktop.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installing Git, restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if .git exists
if (-not (Test-Path ".git")) {
    Write-Host "[INFO] Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Check current remote
$remote = git remote get-url origin 2>$null
if ($remote) {
    Write-Host "[INFO] Current remote: $remote" -ForegroundColor Yellow
    $update = Read-Host "Do you want to update remote to https://github.com/Icansee-you/test1830.git? (y/n)"
    if ($update -eq "y" -or $update -eq "Y") {
        git remote set-url origin https://github.com/Icansee-you/test1830.git
        Write-Host "[OK] Remote updated" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Adding remote repository..." -ForegroundColor Yellow
    git remote add origin https://github.com/Icansee-you/test1830.git
    Write-Host "[OK] Remote added" -ForegroundColor Green
}

# Check if there are uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "[INFO] Staging all files..." -ForegroundColor Yellow
    git add .
    
    Write-Host "[INFO] Creating commit..." -ForegroundColor Yellow
    $commitMessage = Read-Host "Enter commit message (or press Enter for default)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Initial commit: NOS News Aggregator with Streamlit"
    }
    git commit -m $commitMessage
    Write-Host "[OK] Files committed" -ForegroundColor Green
} else {
    Write-Host "[INFO] No changes to commit" -ForegroundColor Yellow
}

# Set branch to main
Write-Host "[INFO] Setting branch to main..." -ForegroundColor Yellow
git branch -M main

# Push to GitHub
Write-Host ""
Write-Host "[INFO] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "You may be prompted for your GitHub credentials." -ForegroundColor Cyan
Write-Host ""

try {
    git push -u origin main
    Write-Host ""
    Write-Host "[SUCCESS] Code pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Go to: https://share.streamlit.io" -ForegroundColor White
    Write-Host "2. Sign in with GitHub" -ForegroundColor White
    Write-Host "3. Click 'New app'" -ForegroundColor White
    Write-Host "4. Select repository: Icansee-you/test1830" -ForegroundColor White
    Write-Host "5. Set main file: streamlit_app.py" -ForegroundColor White
    Write-Host "6. Add secrets (DJANGO_SECRET_KEY, etc.)" -ForegroundColor White
    Write-Host "7. Deploy!" -ForegroundColor White
    Write-Host ""
    Write-Host "See GITHUB_DEPLOYMENT.md for detailed instructions." -ForegroundColor Yellow
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible solutions:" -ForegroundColor Yellow
    Write-Host "1. Check your GitHub credentials" -ForegroundColor White
    Write-Host "2. Make sure you have push access to the repository" -ForegroundColor White
    Write-Host "3. Try using GitHub Desktop instead" -ForegroundColor White
    Write-Host "4. Check your internet connection" -ForegroundColor White
}

