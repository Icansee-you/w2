# Local Testing Guide

This guide explains how to test the app locally without Supabase, then deploy to Streamlit Cloud with Supabase.

## Local Testing (Without Supabase)

### Step 1: Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (Supabase is optional for local testing)
pip install -r requirements.txt
```

**Note**: The app will automatically use local SQLite storage if Supabase credentials are not set.

### Step 2: Run the App Locally

```powershell
streamlit run streamlit_app.py
```

The app will:
- ✅ Use local SQLite database (`local_test.db`)
- ✅ Use JSON file for user preferences (`local_preferences.json`)
- ✅ Show "🧪 Testmodus" indicator in sidebar
- ✅ Work exactly like production, but with local storage

### Step 3: Test Features

1. **Sign up/Login**: 
   - Any email/password works (mock authentication)
   - User preferences are stored locally

2. **Import Articles**:
   - Click "🔄 Artikelen Vernieuwen"
   - Articles are stored in `local_test.db`

3. **Test Blacklist**:
   - Add/remove keywords
   - Verify articles are filtered

4. **Test ELI5**:
   - Generate summaries (if API key provided)
   - Or test without (will use simple extraction)

### Step 4: Local Files Created

When testing locally, these files are created:
- `local_test.db` - SQLite database with articles
- `local_preferences.json` - User preferences

**Note**: Add these to `.gitignore` to avoid committing test data.

## Deploying to Streamlit Cloud (With Supabase)

### Step 1: Set Up Supabase

1. Create project at https://supabase.com
2. Run `supabase_schema.sql` in SQL Editor
3. Get API keys from Project Settings → API

### Step 2: Add Secrets to Streamlit Cloud

1. Go to your app → "Manage app" → "Secrets"
2. Add:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   
   # Optional: For ELI5 generation
   GROQ_API_KEY = "your-groq-key"
   ```

### Step 3: Deploy

```powershell
git add .
git commit -m "Add Supabase integration"
git push
```

The app will automatically:
- ✅ Detect Supabase credentials
- ✅ Switch from local storage to Supabase
- ✅ Use real authentication
- ✅ Store data in Supabase

## How It Works

The app automatically detects which mode to use:

```python
# In supabase_client.py
def get_supabase_client():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if supabase_url and supabase_key:
        # Use Supabase (production)
        return SupabaseClient()
    else:
        # Use local storage (testing)
        return LocalStorage()
```

**Local Mode** (no Supabase credentials):
- Uses SQLite for articles
- Uses JSON for preferences
- Mock authentication (any email/password works)
- Perfect for local testing

**Production Mode** (Supabase credentials set):
- Uses Supabase database
- Real authentication
- Persistent cloud storage
- Full features

## Testing Checklist

### Local Testing
- [ ] App runs without Supabase credentials
- [ ] Can sign up/login (mock)
- [ ] Can import articles from RSS
- [ ] Articles stored in `local_test.db`
- [ ] Blacklist works correctly
- [ ] ELI5 generation works (if API key provided)

### Production Testing
- [ ] Supabase project created
- [ ] Database tables created
- [ ] Secrets added to Streamlit Cloud
- [ ] App connects to Supabase
- [ ] Real authentication works
- [ ] Articles stored in Supabase
- [ ] Blacklist persists across sessions

## Migration from Local to Supabase

If you've tested locally and want to migrate data:

1. **Export local articles** (optional):
   ```python
   import sqlite3
   import json
   
   conn = sqlite3.connect('local_test.db')
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM articles")
   articles = cursor.fetchall()
   # Export to JSON or CSV
   ```

2. **Import to Supabase**:
   - Use the "🔄 Artikelen Vernieuwen" button in production
   - Or write a migration script

3. **User preferences**:
   - Users will need to set preferences again (or migrate from `local_preferences.json`)

## Troubleshooting

### "Error initializing Supabase" (Local)
- This is normal if Supabase credentials aren't set
- App should automatically use local storage
- Check sidebar for "🧪 Testmodus" indicator

### "Table does not exist" (Production)
- Run `supabase_schema.sql` in Supabase SQL Editor
- Verify tables are created

### Local files in Git
- Add to `.gitignore`:
  ```
  local_test.db
  local_preferences.json
  ```

## Best Practice Workflow

1. **Develop locally** (no Supabase needed)
   - Test features
   - Verify functionality
   - Fix bugs

2. **Deploy to Streamlit Cloud** (with Supabase)
   - Add Supabase secrets
   - App automatically switches to production mode
   - Real users can sign up and use the app

This way you can develop and test without needing Supabase, then seamlessly deploy to production!

