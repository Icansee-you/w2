# Quick Reference Guide

## Environment Variables (Streamlit Secrets)

```toml
# Required
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Optional - for ELI5 generation and categorization (priority order)
GROQ_API_KEY = "your-groq-api-key"  # RECOMMENDED: Fast, free, reliable
HUGGINGFACE_API_KEY = "your-hf-key"
OPENAI_API_KEY = "your-openai-key"
CHATLLM_API_KEY = "s2_..."  # Currently not working - use Groq instead
```

## Setup Steps

1. **Create Supabase project** → https://supabase.com
2. **Run SQL schema** → Copy `supabase_schema.sql` to Supabase SQL Editor
3. **Get API keys** → Project Settings → API
4. **Add to Streamlit secrets** → App settings → Secrets
5. **Deploy** → Push to GitHub, Streamlit auto-deploys

## Key Features

### User Authentication
- Sign up with email/password
- Login/logout
- Session persistence

### Blacklist Management
- Default keywords: "Trump", "Rusland", "Soedan", "aanslag"
- Add/remove keywords in sidebar
- Articles with blacklisted keywords are hidden

### ELI5 Summaries
- Auto-generate for new articles (if API key provided)
- Manual generation button in article detail
- Stored in database, shown in expandable section

### Mobile-Friendly
- Responsive layout (4 columns → 1 column on mobile)
- Touch-friendly buttons
- Collapsed sidebar on mobile

## File Structure

```
w2/
├── streamlit_app.py          # Main Streamlit app (NEW)
├── supabase_client.py        # Supabase client wrapper
├── articles_repository.py    # Article operations
├── nlp_utils.py              # ELI5 generation
├── supabase_schema.sql       # Database schema
├── SUPABASE_SETUP.md         # Detailed setup guide
└── IMPLEMENTATION_SUMMARY.md # Code changes summary
```

## Common Tasks

### Import Articles
Click "🔄 Artikelen Vernieuwen" button in sidebar

### Generate ELI5 Summaries
Click "✨ Genereer ELI5 samenvattingen" button in sidebar

### Manage Blacklist
1. Log in
2. Go to sidebar → Voorkeuren
3. Add/remove keywords

### View Article Detail
Click on article title to open full view with ELI5 summary

## Troubleshooting

**"Error initializing Supabase"**
→ Check SUPABASE_URL and SUPABASE_ANON_KEY in secrets

**"Table does not exist"**
→ Run supabase_schema.sql in Supabase SQL Editor

**"No articles showing"**
→ Click "🔄 Artikelen Vernieuwen" to import articles

**"ELI5 not generating"**
→ Add GROQ_API_KEY (get free key from https://console.groq.com/)
→ See GROQ_SETUP.md for detailed instructions

