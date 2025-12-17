# Local ChatLLM Testing Guide

## Quick Start

### Option 1: Set Environment Variable (PowerShell)

```powershell
# Set the API key
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Verify it's set
echo $env:CHATLLM_API_KEY

# Run the test script
python test_chatllm_local.py

# Or run Streamlit app
streamlit run streamlit_app.py
```

### Option 2: Set Environment Variable (Command Prompt)

```cmd
set CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
python test_chatllm_local.py
```

### Option 3: Pass as Command Line Argument

```powershell
python test_chatllm_local.py s2_733cff6da442497eb4f1a5f2e11f9d7a
```

### Option 4: Create .env File

1. Create a `.env` file in the project root:
   ```
   CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
   ```

2. Install python-dotenv (if not already installed):
   ```powershell
   pip install python-dotenv
   ```

3. The app will automatically load it (if configured)

## Step-by-Step Testing

### Step 1: Test ChatLLM API

```powershell
# Set API key
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Run test script
python test_chatllm_local.py
```

**Expected output:**
```
✅ SUCCESS!
Generated Summary: [simple Dutch explanation]
Assigned Categories: [list of categories]
🎉 All tests passed!
```

### Step 2: Run Streamlit App

```powershell
# Make sure API key is still set
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Run app
streamlit run streamlit_app.py
```

### Step 3: Test in App

1. **Import articles**: Click "🔄 Artikelen Vernieuwen"
   - Articles should be automatically categorized using ChatLLM

2. **Generate ELI5**: Click "✨ Genereer ELI5 samenvattingen"
   - Summaries should be generated using ChatLLM

3. **Check article detail**: Click on an article
   - Should show ELI5 summary if generated
   - Should show categories assigned

## Troubleshooting

### "CHATLLM_API_KEY not set"

**Solution:**
```powershell
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"
```

**Note:** Environment variables in PowerShell only last for the current session. To make it permanent, add to your PowerShell profile or use a `.env` file.

### "ChatLLM API error"

**Possible causes:**
- API endpoint might be different
- API key format might be incorrect
- Network/firewall issues

**Solutions:**
1. Check internet connection
2. Verify API key is correct
3. The app will automatically fall back to other APIs or keyword matching

### Test Script Fails

If the test script fails:
1. Check if `requests` library is installed: `pip install requests`
2. Check internet connection
3. Try running with verbose output

The app will still work - it will just use fallback methods (other APIs or keyword matching).

## Making API Key Persistent

### PowerShell Profile (Recommended)

1. Find your profile:
   ```powershell
   echo $PROFILE
   ```

2. Edit the profile:
   ```powershell
   notepad $PROFILE
   ```

3. Add this line:
   ```powershell
   $env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"
   ```

4. Reload profile:
   ```powershell
   . $PROFILE
   ```

### .env File (Alternative)

1. Create `.env` in project root:
   ```
   CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
   ```

2. Install python-dotenv:
   ```powershell
   pip install python-dotenv
   ```

3. The app should automatically load it (if configured in code)

## Verification

After setting up, verify it works:

```powershell
# Check environment variable
echo $env:CHATLLM_API_KEY

# Should output: s2_733cff6da442497eb4f1a5f2e11f9d7a

# Run test
python test_chatllm_local.py

# Should show: ✅ SUCCESS!
```

## Next Steps

Once ChatLLM is working locally:

1. ✅ Test categorization - import articles and check categories
2. ✅ Test ELI5 generation - generate summaries and check quality
3. ✅ Deploy to Streamlit Cloud - add API key to secrets

The app will automatically use ChatLLM when the API key is set!

