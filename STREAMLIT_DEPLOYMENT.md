# Streamlit Cloud Deployment Guide

This guide will help you deploy your NOS News Aggregator to Streamlit Cloud.

## Prerequisites

1. **GitHub Account**: You need a GitHub account
2. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Database**: You'll need to set up a database (PostgreSQL recommended for production, SQLite works for testing)

## Step 1: Prepare Your Repository

### 1.1 Ensure All Files Are Committed

Make sure your repository includes:
- ✅ `streamlit_app.py` - Main Streamlit application
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `requirements.txt` - Python dependencies (includes streamlit)
- ✅ `config/settings.py` - Django settings
- ✅ All Django app files (`apps/`, `config/`, etc.)

### 1.2 Update .gitignore

Ensure `.gitignore` doesn't exclude necessary files. The following should be committed:
- `.streamlit/` directory
- `streamlit_app.py`
- All Python source files

But exclude:
- `venv/`
- `.env` (use Streamlit Cloud secrets instead)
- `db.sqlite3` (if using SQLite locally)
- `__pycache__/`

## Step 2: Push to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Add Streamlit app for deployment"
   ```

2. **Create a GitHub repository**:
   - Go to [github.com](https://github.com)
   - Click "New repository"
   - Name it (e.g., `nos-news-aggregator`)
   - Don't initialize with README (if you already have files)

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Set Up Database

### Option A: PostgreSQL (Recommended for Production)

1. **Set up a PostgreSQL database**:
   - Use services like:
     - [Supabase](https://supabase.com) (free tier available)
     - [ElephantSQL](https://www.elephantsql.com) (free tier available)
     - [Railway](https://railway.app) (free tier available)
     - [Render](https://render.com) (free tier available)

2. **Get your database URL**:
   - Format: `postgres://username:password@host:port/database`
   - Example: `postgres://user:pass@db.example.com:5432/newsdb`

### Option B: SQLite (For Testing)

SQLite works for testing but has limitations:
- File-based database (not ideal for cloud)
- Limited concurrent access
- Not recommended for production

## Step 4: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App**:
   - Click "New app"
   - Select your repository
   - Select the branch (usually `main`)
   - Set **Main file path**: `streamlit_app.py`

3. **Configure Secrets**:
   Click "Advanced settings" and add secrets in TOML format:

   ```toml
   # For PostgreSQL
   DATABASE_URL = "postgres://username:password@host:port/database"
   
   # For SQLite (not recommended for production)
   # DATABASE_URL = ""  # Leave empty to use SQLite
   
   # Django settings
   DJANGO_SECRET_KEY = "your-very-long-random-secret-key-here"
   DEBUG = "False"
   ALLOWED_HOSTS = "localhost,127.0.0.1"
   
   # Optional: Redis (if using Celery)
   REDIS_URL = "redis://your-redis-host:6379/0"
   ```

   **How to generate a secret key**:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Deploy**:
   - Click "Deploy"
   - Wait for the app to build and deploy

## Step 5: Initialize Database

After deployment, you need to initialize the database:

### Option 1: Using Streamlit Cloud Console (Recommended)

1. Go to your app settings in Streamlit Cloud
2. Open the "Manage app" menu
3. Use the console/terminal to run:
   ```bash
   python setup_streamlit_db.py
   ```

### Option 2: Using Local Setup Script

1. Clone your repository locally
2. Set up environment variables
3. Run:
   ```bash
   python setup_streamlit_db.py
   ```

### Option 3: Manual Setup via Django Management Commands

If you have access to run Django commands:

```bash
# Run migrations
python manage.py migrate

# Initialize categories
python manage.py init_categories

# Import articles (optional)
python manage.py ingest_nos --max-items 100
```

## Step 6: Import News Articles

To populate the database with articles:

### Option 1: Using Django Management Command (Local)

Run locally with database connection:
```bash
python manage.py ingest_nos --max-items 100
```

### Option 2: Using Celery (If Redis is configured)

If you've set up Redis and Celery:
- The app will automatically fetch articles every 8 hours
- Or trigger manually via Django admin

### Option 3: Manual Import Script

Create a script that connects to your production database and imports articles.

## Step 7: Verify Deployment

1. **Check the app loads**: Visit your Streamlit Cloud URL
2. **Check categories**: Should see categories in the sidebar
3. **Check articles**: If articles are imported, they should display
4. **Test filters**: Try filtering by category
5. **Test search**: Try searching for articles

## Troubleshooting

### Database Connection Errors

**Error**: `django.db.utils.OperationalError: could not connect to server`

**Solutions**:
- Verify `DATABASE_URL` in Streamlit secrets is correct
- Check database allows connections from Streamlit Cloud IPs
- For PostgreSQL, ensure SSL is enabled if required:
  - Add `?sslmode=require` to your DATABASE_URL

### No Categories Found

**Error**: "Geen categorieën gevonden"

**Solution**:
- Run `python setup_streamlit_db.py` or `python manage.py init_categories`
- Check database connection is working

### No Articles Found

**Error**: "Geen artikelen gevonden"

**Solution**:
- Import articles using `python manage.py ingest_nos`
- Check database has articles: `Article.objects.count()`

### Import Errors

**Error**: Module not found or Django setup errors

**Solution**:
- Ensure all dependencies are in `requirements.txt`
- Check `streamlit_app.py` properly initializes Django
- Verify file structure matches expected paths

### Static Files Issues

**Note**: Streamlit apps don't use Django's static files system. All styling is handled by Streamlit.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes* | Database connection string | `postgres://user:pass@host:5432/db` |
| `DJANGO_SECRET_KEY` | Yes | Django secret key | Generated random string |
| `DEBUG` | No | Debug mode (False for production) | `False` |
| `ALLOWED_HOSTS` | No | Allowed hosts (comma-separated) | `localhost,127.0.0.1` |
| `REDIS_URL` | No | Redis connection (for Celery) | `redis://host:6379/0` |

*Required if using PostgreSQL. Leave empty for SQLite (not recommended).

## Database Setup Options

### Using Supabase (Free Tier)

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string
5. Format: `postgres://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

### Using ElephantSQL (Free Tier)

1. Sign up at [elephantsql.com](https://www.elephantsql.com)
2. Create a new instance
3. Copy the connection URL from the instance details

### Using Railway (Free Tier)

1. Sign up at [railway.app](https://railway.app)
2. Create a new PostgreSQL service
3. Copy the connection string from the service variables

## Updating Your App

1. **Make changes** to your code locally
2. **Test locally**:
   ```bash
   streamlit run streamlit_app.py
   ```
3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Update app"
   git push
   ```
4. **Streamlit Cloud will automatically redeploy**

## Manual Database Operations

If you need to run Django management commands on the production database:

1. Set environment variables locally to point to production database
2. Run commands:
   ```bash
   python manage.py migrate
   python manage.py init_categories
   python manage.py ingest_nos
   ```

## Security Notes

- ✅ Never commit `.env` files to Git
- ✅ Use Streamlit Cloud secrets for sensitive data
- ✅ Use strong `DJANGO_SECRET_KEY` in production
- ✅ Set `DEBUG=False` in production
- ✅ Use PostgreSQL with SSL in production
- ✅ Regularly update dependencies

## Support

- Streamlit Cloud Docs: [docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- Django Docs: [docs.djangoproject.com](https://docs.djangoproject.com)
- Streamlit Forums: [discuss.streamlit.io](https://discuss.streamlit.io)

## Next Steps

After successful deployment:

1. ✅ Set up automatic article ingestion (via Celery or scheduled tasks)
2. ✅ Monitor app performance
3. ✅ Set up database backups
4. ✅ Configure custom domain (if needed)
5. ✅ Add analytics (optional)


