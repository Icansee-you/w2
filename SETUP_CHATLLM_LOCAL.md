# Quick Setup: Test ChatLLM Locally

## Fastest Way (PowerShell)

```powershell
# 1. Set API key for this session
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# 2. Test the API
python test_chatllm_local.py

# 3. Run the app
streamlit run streamlit_app.py
```

## What to Expect

### Test Script Output

If ChatLLM API works:
```
[SUCCESS] ELI5 summary generated!
Generated Summary: [simple Dutch explanation]
[SUCCESS] All tests passed!
```

If ChatLLM API doesn't work (that's OK!):
```
[ERROR] ChatLLM API is not working
[WARNING] The app will still work using fallback methods
```

**Note:** Even if ChatLLM doesn't work, the app will automatically use:
- Other LLM APIs (Groq, Hugging Face, OpenAI)
- Keyword-based categorization (always works)
- Simple text extraction for ELI5

## Making It Permanent

### Option 1: PowerShell Profile

```powershell
# Edit your profile
notepad $PROFILE

# Add this line:
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Reload
. $PROFILE
```

### Option 2: .env File

Create `.env` in project root:
```
CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
```

## Testing in the App

1. **Set API key** (see above)
2. **Run app**: `streamlit run streamlit_app.py`
3. **Import articles**: Click "🔄 Artikelen Vernieuwen"
   - Articles will be categorized (using ChatLLM if available)
4. **Generate ELI5**: Click "✨ Genereer ELI5 samenvattingen"
   - Summaries will use ChatLLM if available

## Troubleshooting

**"Failed to resolve 'api.aitomatic.com'"**
- The API endpoint might be different
- The app will automatically try multiple endpoints
- Falls back to other APIs if ChatLLM doesn't work

**"No summary generated"**
- ChatLLM might not be accessible
- App will use other APIs or simple extraction
- Everything still works!

**The app works fine without ChatLLM** - it's just an enhancement, not required!

