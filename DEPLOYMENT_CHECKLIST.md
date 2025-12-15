# Deployment Checklist for test1830

## Repository: https://github.com/Icansee-you/test1830

Use this checklist to ensure everything is ready for deployment.

## Pre-Deployment Checklist

### ✅ Code Ready
- [ ] All files are saved
- [ ] `streamlit_app.py` exists and works locally
- [ ] `requirements.txt` includes all dependencies
- [ ] `.streamlit/config.toml` is configured
- [ ] Database auto-initialization is working (in streamlit_app.py)

### ✅ Git Setup
- [ ] Git is installed (or GitHub Desktop)
- [ ] `.gitignore` excludes sensitive files (venv, .env, db.sqlite3)
- [ ] All necessary files are ready to commit

### ✅ Files to Commit
- [x] `streamlit_app.py` - Main Streamlit app
- [x] `requirements.txt` - Dependencies
- [x] `.streamlit/config.toml` - Streamlit config
- [x] `config/settings.py` - Django settings (with optional dotenv)
- [x] `config/__init__.py` - Django config (with optional Celery)
- [x] `apps/` - All Django apps
- [x] `setup_streamlit_db.py` - Database setup script
- [x] `manage.py` - Django management
- [x] All other necessary Django files

### ✅ Files NOT to Commit (should be in .gitignore)
- [x] `venv/` - Virtual environment
- [x] `.env` - Local environment variables
- [x] `db.sqlite3` - Local database
- [x] `__pycache__/` - Python cache

## Deployment Steps

### Step 1: Push to GitHub

**Option A: Use the script**
```powershell
.\push_to_github.ps1
```

**Option B: Manual commands**
```powershell
git init
git add .
git commit -m "Initial commit: NOS News Aggregator with Streamlit"
git remote add origin https://github.com/Icansee-you/test1830.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - URL: https://share.streamlit.io
   - Sign in with GitHub

2. **Create New App**
   - Click "New app"
   - **Repository**: `Icansee-you/test1830`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets** (Critical!)
   - Click "Advanced settings" → "Secrets"
   - Add these secrets:
     ```toml
     DJANGO_SECRET_KEY = "generate-a-random-secret-key-here"
     DEBUG = "False"
     ALLOWED_HOSTS = "localhost,127.0.0.1"
     ```
   - **Generate secret key**:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

4. **Wait for Deployment**
   - Streamlit will install dependencies
   - App will start automatically
   - Database will auto-initialize on first run

### Step 3: Verify Deployment

- [ ] App loads at Streamlit Cloud URL
- [ ] No errors in the app
- [ ] Categories appear in sidebar (5 categories)
- [ ] Articles display (if you have articles)
- [ ] Search works
- [ ] Filters work

## Post-Deployment

### Optional: Import Articles

If you want to import articles to the cloud database:

1. **Option 1: Use local database** (if you have articles locally)
   - Export from local database
   - Import to cloud database

2. **Option 2: Use Django management command** (if you have shell access)
   ```bash
   python manage.py ingest_nos --max-items 100
   ```

3. **Option 3: Set up automatic ingestion**
   - Configure Celery/Redis (if available)
   - Or use scheduled tasks

### Optional: Set Up PostgreSQL

For production, consider using PostgreSQL instead of SQLite:

1. **Create free PostgreSQL database**:
   - Supabase: https://supabase.com
   - ElephantSQL: https://www.elephantsql.com
   - Railway: https://railway.app

2. **Add to Streamlit secrets**:
   ```toml
   DATABASE_URL = "postgres://user:password@host:port/database"
   ```

3. **Redeploy** - Streamlit will use PostgreSQL automatically

## Troubleshooting

### App won't deploy
- [ ] Check `requirements.txt` has all dependencies
- [ ] Verify `streamlit_app.py` is in root directory
- [ ] Check Streamlit Cloud logs for errors

### "No categories found"
- [ ] Wait for first page load (auto-initialization should run)
- [ ] Check Streamlit Cloud logs
- [ ] Verify database connection

### Database errors
- [ ] Check `DATABASE_URL` in secrets (if using PostgreSQL)
- [ ] Verify database is accessible
- [ ] Check Streamlit Cloud logs

## Your App URL

After successful deployment, your app will be at:
```
https://test1830.streamlit.app
```

## Need Help?

- See `GITHUB_DEPLOYMENT.md` for detailed instructions
- See `STREAMLIT_DEPLOYMENT.md` for general deployment guide
- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud

