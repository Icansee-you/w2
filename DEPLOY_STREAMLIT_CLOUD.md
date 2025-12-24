# Deploy to Streamlit Cloud - Step by Step Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (free at https://streamlit.io/cloud)
- All your API keys ready (Supabase, Groq, etc.)

## Step 1: Prepare Your Repository

### 1.1 Ensure .gitignore is correct
Make sure `.gitignore` includes:
- `.env` (never commit API keys!)
- `venv/`
- `__pycache__/`
- `.last_fetch_time`
- `local_test.db`
- `local_preferences.json`

### 1.2 Check requirements.txt
Make sure `requirements.txt` includes all dependencies:
```bash
streamlit
supabase
python-dotenv
feedparser
beautifulsoup4
requests
dateutil
pytz
```

## Step 2: Push to GitHub

### 2.1 Initialize Git (if not already done)
```bash
git init
git add .
git commit -m "Initial commit: NOS News Aggregator"
```

### 2.2 Create GitHub Repository
1. Go to https://github.com/new
2. Create a new repository (e.g., `nos-news-aggregator`)
3. **DO NOT** initialize with README, .gitignore, or license

### 2.3 Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/nos-news-aggregator.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

### 3.1 Sign in to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"

### 3.2 Configure Your App
- **Repository**: Select your GitHub repository
- **Branch**: `main` (or your default branch)
- **Main file path**: `streamlit_app.py`
- **App URL**: Choose a custom subdomain (e.g., `nos-news-aggregator`)

### 3.3 Set Environment Variables (Secrets)
In Streamlit Cloud, go to "Settings" → "Secrets" and add:

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_ANON_KEY = "your-supabase-anon-key"
GROQ_API_KEY = "your-groq-api-key"
OPENAI_API_KEY = "your-openai-api-key"  # Optional
HUGGINGFACE_API_KEY = "your-huggingface-api-key"  # Optional
CHATLLM_API_KEY = "your-chatllm-api-key"  # Optional
```

**Important**: Never commit these to GitHub! Only add them in Streamlit Cloud secrets.

### 3.4 Deploy
Click "Deploy" and wait for the app to build and deploy.

## Step 4: Verify Deployment

1. Check the deployment logs for any errors
2. Visit your app URL (e.g., `https://nos-news-aggregator.streamlit.app`)
3. Test login and functionality

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check `requirements.txt` has all dependencies
   - Check import paths are correct

2. **API Key Errors**
   - Verify all secrets are set in Streamlit Cloud
   - Check secret names match exactly (case-sensitive)

3. **Database Connection Issues**
   - Verify Supabase URL and key are correct
   - Check Supabase project is active

4. **Background Scheduler**
   - The background scheduler will run automatically on Streamlit Cloud
   - Check logs if articles aren't updating

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] User login works
- [ ] Articles display correctly
- [ ] Category filtering works
- [ ] Background scheduler is running (check logs)
- [ ] All API integrations work (LLM categorization, etc.)

## Updating Your App

After making changes:
1. Commit and push to GitHub
2. Streamlit Cloud will automatically redeploy
3. Check deployment status in Streamlit Cloud dashboard

