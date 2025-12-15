# Deploy to GitHub and Streamlit Cloud

## Repository: https://github.com/Icansee-you/test1830

This guide will help you push your code to GitHub and deploy to Streamlit Cloud.

## Step 1: Install Git (if not installed)

### Option A: Install Git for Windows
1. Download from: https://git-scm.com/download/win
2. Install with default settings
3. Restart PowerShell after installation

### Option B: Use GitHub Desktop
1. Download from: https://desktop.github.com/
2. Sign in with your GitHub account
3. Use the GUI to push your code

## Step 2: Push Code to GitHub

### Using Git Command Line (if Git is installed):

Open PowerShell in the project directory (`C:\Users\Chris\Desktop\NEWCO\w2`) and run:

```powershell
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: NOS News Aggregator with Streamlit"

# Add your GitHub repository as remote
git remote add origin https://github.com/Icansee-you/test1830.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note**: You may be prompted for your GitHub username and password (or personal access token).

### Using GitHub Desktop:

1. Open GitHub Desktop
2. Click "File" → "Add Local Repository"
3. Browse to: `C:\Users\Chris\Desktop\NEWCO\w2`
4. Click "Publish repository"
5. Select the repository: `Icansee-you/test1830`
6. Click "Publish repository"

## Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Community Cloud**:
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App**:
   - Click "New app" button
   - **Repository**: Select `Icansee-you/test1830`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets** (Important!):
   - After clicking "Deploy", click on "Advanced settings"
   - Click "Secrets" tab
   - Add the following secrets in TOML format:

   ```toml
   # Required: Django secret key (generate a random string)
   DJANGO_SECRET_KEY = "django-insecure-change-this-to-a-very-long-random-string-in-production"
   
   # Optional: Set to False for production
   DEBUG = "False"
   
   # Optional: Allowed hosts (comma-separated)
   ALLOWED_HOSTS = "localhost,127.0.0.1"
   
   # Optional: Database URL (leave empty to use SQLite, or use PostgreSQL)
   # DATABASE_URL = "postgres://user:password@host:port/database"
   ```

   **How to generate a secure secret key:**
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Save and Deploy**:
   - Click "Save" in secrets
   - The app will automatically redeploy

## Step 4: Wait for Deployment

- Streamlit Cloud will:
  1. Install dependencies from `requirements.txt`
  2. Run your `streamlit_app.py`
  3. The app will automatically initialize the database on first run (migrations and categories)

- You'll see a public URL like: `https://test1830.streamlit.app`

## Step 5: Verify Deployment

1. **Check the app loads**: Visit your Streamlit Cloud URL
2. **Check categories**: Should see 5 categories in the sidebar
3. **Check articles**: If you have articles in your database, they should display

**Note**: If you see "No categories found", the auto-initialization should run on the first page load. If it doesn't work, you may need to manually run migrations (see troubleshooting below).

## Troubleshooting

### "No categories found" after deployment

The app should auto-initialize, but if it doesn't:

1. **Option 1: Use Streamlit Cloud's built-in terminal** (if available):
   - Go to your app settings
   - Look for "Manage app" → "Terminal" or "Console"
   - Run: `python setup_streamlit_db.py`

2. **Option 2: Run locally against cloud database**:
   - Set `DATABASE_URL` in your local `.env` to point to your cloud database
   - Run: `python setup_streamlit_db.py`

3. **Option 3: Import articles manually**:
   - If you have access to run Django commands, run:
   ```bash
   python manage.py ingest_nos --max-items 100
   ```

### Database Issues

**For SQLite (default)**:
- Works out of the box
- Data persists between deployments
- Good for testing/small apps

**For PostgreSQL (recommended for production)**:
- Set up a free PostgreSQL database:
  - [Supabase](https://supabase.com) - Free tier
  - [ElephantSQL](https://www.elephantsql.com) - Free tier
  - [Railway](https://railway.app) - Free tier
- Add `DATABASE_URL` to Streamlit secrets:
  ```toml
  DATABASE_URL = "postgres://user:password@host:port/database"
  ```

### Build Errors

If deployment fails:
1. Check `requirements.txt` includes all dependencies
2. Verify `streamlit_app.py` is in the root directory
3. Check Streamlit Cloud logs for specific errors

## Files That Should Be in Your Repository

Make sure these files are committed:
- ✅ `streamlit_app.py` (main app file)
- ✅ `requirements.txt` (dependencies)
- ✅ `.streamlit/config.toml` (Streamlit config)
- ✅ `config/settings.py` (Django settings)
- ✅ `apps/` directory (all Django apps)
- ✅ `setup_streamlit_db.py` (database setup script)
- ✅ `manage.py` (Django management)

**Files that should NOT be committed** (should be in `.gitignore`):
- ❌ `venv/` (virtual environment)
- ❌ `.env` (local environment variables - use Streamlit secrets instead)
- ❌ `db.sqlite3` (local database - will be created on Streamlit Cloud)
- ❌ `__pycache__/` (Python cache)

## Next Steps After Deployment

1. **Test your app**: Visit the public URL and test all features
2. **Import articles** (if needed): Use Django management commands or set up automatic ingestion
3. **Customize**: Update the app appearance, add features, etc.
4. **Share**: Share your public URL with others!

## Your Streamlit Cloud URL

After deployment, your app will be available at:
```
https://test1830.streamlit.app
```

(Or similar, depending on your app name)

## Need Help?

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud
- GitHub Docs: https://docs.github.com
- Django Docs: https://docs.djangoproject.com

