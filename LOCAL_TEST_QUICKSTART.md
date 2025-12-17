# Quick Start: Local Testing

## Test Locally (No Supabase Needed!)

### Step 1: Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Note**: Supabase is optional - the app will use local SQLite if Supabase credentials aren't set.

### Step 2: Run the App

```powershell
streamlit run streamlit_app.py
```

That's it! The app will:
- ✅ Automatically use local SQLite database
- ✅ Show "🧪 Testmodus" in sidebar
- ✅ Work exactly like production, but with local storage

### Step 3: Test Features

1. **Sign up/Login**: Any email/password works (e.g., `test@test.com` / `password123`)
2. **Import articles**: Click "🔄 Artikelen Vernieuwen"
3. **Test blacklist**: Add/remove keywords in sidebar
4. **Test ELI5**: Generate summaries (if API key provided)

### Local Files Created

- `local_test.db` - SQLite database (articles)
- `local_preferences.json` - User preferences

These are automatically ignored by Git (already in `.gitignore`).

## Deploy to Streamlit Cloud (With Supabase)

### Step 1: Set Up Supabase (One Time)

1. Create project: https://supabase.com
2. Run SQL: Copy `supabase_schema.sql` → Supabase SQL Editor → Run
3. Get keys: Project Settings → API → Copy URL and anon key

### Step 2: Add Secrets to Streamlit Cloud

1. App → "Manage app" → "Secrets"
2. Add:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJ..."
   ```

### Step 3: Deploy

```powershell
git add .
git commit -m "Ready for production with Supabase"
git push
```

The app automatically detects Supabase credentials and switches to production mode!

## How It Works

**Local (no Supabase credentials)**:
- Uses `local_storage.py` → SQLite + JSON
- Mock authentication
- Perfect for testing

**Production (Supabase credentials set)**:
- Uses `supabase_client.py` → Supabase
- Real authentication
- Cloud storage

The switch is **automatic** - no code changes needed!

## Troubleshooting

**"Error initializing Supabase" locally?**
- This is normal! App falls back to local storage automatically
- Look for "🧪 Testmodus" in sidebar

**Want to test with Supabase locally?**
- Create `.env` file:
  ```env
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_ANON_KEY=eyJ...
  ```
- App will use Supabase instead of local storage

