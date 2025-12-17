# Supabase Setup Guide

This guide will help you set up Supabase for the NOS News Aggregator with user authentication and database.

## Step 1: Create Supabase Project

1. **Sign up/Login**: Go to https://supabase.com
2. **Create New Project**:
   - Click "New Project"
   - Choose organization
   - Project name: `nos-news-aggregator` (or your choice)
   - Database password: **Save this password!**
   - Region: Choose closest to you
   - Click "Create new project"
   - Wait 2-3 minutes for setup

## Step 2: Get API Keys

1. **Go to Project Settings**:
   - Click the gear icon (⚙️) in the left sidebar
   - Click "API"

2. **Copy the following**:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: Long string starting with `eyJ...`
   - **service_role key**: Long string (keep this secret!)

## Step 3: Set Up Database Tables

1. **Go to SQL Editor**:
   - Click "SQL Editor" in left sidebar
   - Click "New query"

2. **Run the Schema**:
   - Open `supabase_schema.sql` from this project
   - Copy all contents
   - Paste into SQL Editor
   - Click "Run" (or press Ctrl+Enter)

3. **Verify Tables Created**:
   - Go to "Table Editor" in left sidebar
   - You should see:
     - `articles` table
     - `user_preferences` table

## Step 4: Configure Authentication

1. **Enable Email Auth** (usually enabled by default):
   - Go to "Authentication" → "Providers"
   - Ensure "Email" is enabled
   - Configure email templates if needed

2. **Optional: Enable Magic Link**:
   - In "Email" provider settings
   - Enable "Enable email confirmations" (optional)
   - Enable "Magic Link" if you want passwordless login

## Step 5: Configure Streamlit Cloud Secrets

1. **Go to Streamlit Cloud**:
   - Open your app settings
   - Click "Secrets"

2. **Add the following secrets**:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   
   # Optional: For ELI5 generation and categorization (priority order)
   CHATLLM_API_KEY = "s2_733cff6da442497eb4f1a5f2e11f9d7a"  # Highest priority
   GROQ_API_KEY = "your-groq-key"  # Optional
   HUGGINGFACE_API_KEY = "your-huggingface-key"  # Optional
   OPENAI_API_KEY = "your-openai-key"  # Optional
   ```

3. **Save** and the app will redeploy

## Step 6: Test the Setup

1. **Deploy and test**:
   - App should automatically connect to Supabase
   - Try signing up a new user
   - Try adding articles via "🔄 Artikelen Vernieuwen"
   - Check Supabase dashboard to see data

## Database Schema Overview

### `articles` Table
- `id` (UUID) - Primary key
- `stable_id` (TEXT, UNIQUE) - Stable identifier from RSS (guid/hash)
- `title` (TEXT) - Article title
- `description` (TEXT) - Article summary/description
- `url` (TEXT) - Original article URL
- `source` (TEXT) - Source name (default: "NOS")
- `published_at` (TIMESTAMPTZ) - Publication date
- `full_content` (TEXT) - Full article content
- `image_url` (TEXT) - Article image URL
- `category` (TEXT) - Article category
- `eli5_summary_nl` (TEXT) - ELI5 summary in Dutch
- `created_at` (TIMESTAMPTZ) - When added to database
- `updated_at` (TIMESTAMPTZ) - Last update time

### `user_preferences` Table
- `id` (UUID) - Primary key
- `user_id` (UUID, UNIQUE) - Supabase Auth user ID
- `blacklist_keywords` (TEXT[]) - Array of blacklisted keywords
- `created_at` (TIMESTAMPTZ) - When created
- `updated_at` (TIMESTAMPTZ) - Last update time

## Troubleshooting

### "Error initializing Supabase"
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set correctly
- Verify keys are from the same project
- Check for typos in secrets

### "Table does not exist"
- Run the SQL schema in Supabase SQL Editor
- Check table names match exactly

### "Authentication failed"
- Verify email/password format
- Check Supabase Auth is enabled
- Check email confirmation settings (if enabled)

### "Articles not showing"
- Check if articles table has data
- Verify RLS policies allow reading
- Check blacklist isn't filtering everything

## Next Steps

1. **Import initial articles**: Click "🔄 Artikelen Vernieuwen" in the app
2. **Set up ELI5 generation**: Add an LLM API key to secrets (optional)
3. **Customize**: Adjust categories, blacklist defaults, etc.

## Accessing Your Database

### Via Supabase Dashboard
- Go to "Table Editor" to browse data
- Use "SQL Editor" to run queries
- Check "Authentication" → "Users" to see registered users

### Via Python
```python
from supabase_client import get_supabase_client

supabase = get_supabase_client()
articles = supabase.get_articles(limit=10)
print(f"Found {len(articles)} articles")
```

## Security Notes

- ✅ **anon key** is safe to use in frontend (has RLS protection)
- ⚠️ **service_role key** should NEVER be exposed in frontend
- ✅ RLS policies protect user data
- ✅ Passwords are hashed by Supabase Auth

