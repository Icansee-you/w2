# Supabase Setup - Step by Step Guide

## Your Supabase Project Info

From your connection string, I can see:
- **Project Reference**: `skfizxuvxenrltqdwkha`
- **Supabase URL**: `https://skfizxuvxenrltqdwkha.supabase.co`

## Step 1: Get Your Supabase API Keys

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard
2. **Select your project** (the one with reference `skfizxuvxenrltqdwkha`)
3. **Go to Project Settings**:
   - Click the ⚙️ gear icon in the left sidebar
   - Click "API"
4. **Copy these values**:
   - **Project URL**: `https://skfizxuvxenrltqdwkha.supabase.co`
   - **anon/public key**: Long string starting with `eyJ...` (this is what we need for the app)

## Step 2: Set Up Database Tables

1. **Go to SQL Editor** in your Supabase dashboard:
   - Click "SQL Editor" in the left sidebar
   - Click "New query"

2. **Run the schema**:
   - Open `supabase_schema.sql` from this project
   - Copy ALL the SQL code
   - Paste it into the SQL Editor
   - Click "Run" (or press Ctrl+Enter)

3. **Verify tables were created**:
   - Go to "Table Editor" in the left sidebar
   - You should see:
     - ✅ `articles` table
     - ✅ `user_preferences` table

## Step 3: Configure Your Local App

### Option A: Create .env File (Recommended)

Create a `.env` file in the project root with:

```env
# Supabase Configuration
SUPABASE_URL=https://skfizxuvxenrltqdwkha.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# LLM API Keys (already configured)
GROQ_API_KEY=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
CHATLLM_API_KEY=s2_156073f76d354d72a6b0fb22c94a2f8d
```

**Replace `your-anon-key-here` with the anon key from Step 1.**

### Option B: Set Environment Variables (PowerShell)

```powershell
$env:SUPABASE_URL="https://skfizxuvxenrltqdwkha.supabase.co"
$env:SUPABASE_ANON_KEY="your-anon-key-here"
```

## Step 4: Test the Connection

1. **Run the app**:
   ```powershell
   .\run_streamlit.ps1
   ```

2. **Check the console output**:
   - Should show: `[INFO] Supabase credentials detected - using Supabase database`
   - Should NOT show: `🧪 Testmodus` (that means local storage)

3. **Test in the app**:
   - Try signing up a new user
   - Import some articles
   - Check Supabase dashboard → Table Editor → `articles` table to see the data

## Step 5: Verify Everything Works

✅ **Database tables exist** (check in Supabase Table Editor)
✅ **App connects to Supabase** (no "Testmodus" message)
✅ **Can sign up/login** (real authentication)
✅ **Articles are stored** (visible in Supabase dashboard)
✅ **User preferences work** (blacklist, categories)

## Troubleshooting

**"Error initializing Supabase"**
- Double-check the anon key is correct (should start with `eyJ...`)
- Make sure the URL is exactly: `https://skfizxuvxenrltqdwkha.supabase.co`
- Check internet connection

**"Table does not exist"**
- Make sure you ran `supabase_schema.sql` in SQL Editor
- Check Table Editor to verify tables exist

**Still using local storage?**
- Check that `.env` file exists and has correct values
- Or verify environment variables are set: `echo $env:SUPABASE_URL`

## Next Steps

Once everything is working:
- Your data will persist in Supabase cloud database
- You can access it from anywhere
- Ready for production deployment!

