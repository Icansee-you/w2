# ChatLLM API Setup Guide

## Overview

ChatLLM API from Aitomatic is now integrated as the **highest priority** option for both:
- **ELI5 Summary Generation** - Simple, child-friendly explanations
- **Article Categorization** - Automatic multi-category assignment

## API Key

Your ChatLLM API key: `s2_733cff6da442497eb4f1a5f2e11f9d7a`

## Configuration

### For Local Testing

Create a `.env` file in your project root:

```env
CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
```

Or set it in your environment:

```powershell
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"
```

### For Streamlit Cloud

1. Go to your app → "Manage app" → "Secrets"
2. Add:

```toml
CHATLLM_API_KEY = "s2_733cff6da442497eb4f1a5f2e11f9d7a"
```

## How It Works

### Priority Order

The system tries APIs in this order:

1. **ChatLLM** (if `CHATLLM_API_KEY` is set) ⭐ **Highest Priority**
2. Hugging Face (if `HUGGINGFACE_API_KEY` is set)
3. Groq (if `GROQ_API_KEY` is set)
4. OpenAI-compatible (if `OPENAI_API_KEY` is set)
5. Keyword-based fallback (always works, no API needed)

### ELI5 Summaries

When generating ELI5 summaries:
- Uses ChatLLM if API key is set
- Generates simple, child-friendly Dutch explanations
- Explains capitalized words/names that might be unknown
- Falls back to other APIs or simple extraction if ChatLLM fails

### Categorization

When categorizing articles:
- Uses ChatLLM if API key is set
- Analyzes article content to assign multiple categories
- Falls back to keyword matching if ChatLLM fails

## API Endpoints

The integration tries these endpoints (in order):

1. `https://api.aitomatic.com/v1/chat/completions` (primary)
2. `https://chatllm.aitomatic.com/api/v1/chat` (alternative)

If the primary endpoint doesn't work, it automatically tries the alternative.

## Testing

### Test ELI5 Generation

1. Run the app: `streamlit run streamlit_app.py`
2. Import some articles
3. Click "✨ Genereer ELI5 samenvattingen" in sidebar
4. Check if summaries are generated using ChatLLM

### Test Categorization

1. Import articles from RSS feeds
2. Articles should be automatically categorized
3. Check article categories in the database or UI

## Troubleshooting

### "ChatLLM API error"

**Possible causes:**
- API key is incorrect
- API endpoint has changed
- Rate limits exceeded
- Network issues

**Solutions:**
- Verify API key is correct
- Check Aitomatic documentation for current endpoint
- System will automatically fall back to other APIs or keyword matching

### API Not Working

The system is designed to be resilient:
- If ChatLLM fails, it tries other APIs
- If all APIs fail, it uses keyword-based categorization
- ELI5 summaries fall back to simple extraction

### Rate Limits

If you hit rate limits:
- The system will automatically try other APIs
- Consider adding other API keys as backups
- Keyword-based fallback always works

## Benefits of ChatLLM

1. **High Quality**: Better categorization and summaries
2. **Priority**: Used first if API key is set
3. **Resilient**: Falls back gracefully if unavailable
4. **Multi-purpose**: Used for both categorization and ELI5

## Next Steps

1. **Set the API key** in environment variables or Streamlit secrets
2. **Test locally** to verify it works
3. **Deploy to Streamlit Cloud** with the API key in secrets
4. **Monitor** - Check logs if issues occur

The integration is ready to use! Just set the `CHATLLM_API_KEY` environment variable.

