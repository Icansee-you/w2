# Using Supabase Locally

## Yes, you can use Supabase while running locally! ✅

The app automatically detects Supabase credentials and uses Supabase if available, otherwise falls back to local SQLite storage.

## Quick Setup

### Option 1: Set Environment Variables (PowerShell)

```powershell
# Set Supabase credentials
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_ANON_KEY="your-anon-key-here"

# Run the app
.\run_streamlit.ps1
```

### Option 2: Create .env File (Recommended)

1. Create a `.env` file in the project root:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   
   # LLM API keys (already set in run script)
   GROQ_API_KEY=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
   CHATLLM_API_KEY=s2_156073f76d354d72a6b0fb22c94a2f8d
   ```

2. The app will automatically load it (python-dotenv is installed)

### Option 3: Update run_streamlit.ps1

Add your Supabase credentials to the run script (see below)

## Getting Your Supabase Credentials

1. **Go to your Supabase project**: https://supabase.com
2. **Project Settings** → **API**
3. **Copy**:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: Long string starting with `eyJ...`

## Setup Database Tables

Before using Supabase, make sure the tables exist:

1. **Go to Supabase SQL Editor**
2. **Run** the SQL from `supabase_schema.sql`
3. **Verify** tables exist: `articles` and `user_preferences`

## How It Works

The app checks for Supabase credentials:

```python
# In supabase_client.py
if SUPABASE_URL and SUPABASE_ANON_KEY are set:
    → Use Supabase (cloud database)
else:
    → Use LocalStorage (SQLite + JSON files)
```

## Benefits of Using Supabase Locally

✅ **Real authentication** - Test actual user signup/login
✅ **Persistent data** - Data survives app restarts
✅ **Same as production** - Test with the same database
✅ **Multi-device** - Access from multiple devices
✅ **Easy migration** - No need to migrate data later

## Switching Between Local and Supabase

**To use Supabase:**
- Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` environment variables

**To use local storage:**
- Remove or unset `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- App automatically falls back to SQLite

## Troubleshooting

**"Error initializing Supabase"**
- Check that `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
- Verify tables exist in Supabase (run `supabase_schema.sql`)
- Check internet connection

**"Tables don't exist"**
- Run `supabase_schema.sql` in Supabase SQL Editor
- Verify in Table Editor that `articles` and `user_preferences` exist

**Want to test without Supabase?**
- Simply don't set the environment variables
- App will use local storage automatically

