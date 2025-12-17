# Testing ChatLLM Locally

## Quick Start

### Option 1: Use the Test Script (Easiest)

**Windows (PowerShell):**
```powershell
.\test_chatllm_local.ps1
```

**Mac/Linux:**
```bash
chmod +x test_chatllm_local.sh
./test_chatllm_local.sh
```

### Option 2: Manual Setup

**Windows (PowerShell):**
```powershell
# Set the API key
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Activate virtual environment (if you have one)
.\venv\Scripts\Activate.ps1

# Run Streamlit
streamlit run streamlit_app.py
```

**Mac/Linux:**
```bash
# Set the API key
export CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Activate virtual environment (if you have one)
source venv/bin/activate

# Run Streamlit
streamlit run streamlit_app.py
```

### Option 3: Create .env File

Create a `.env` file in your project root:

```env
CHATLLM_API_KEY=s2_733cff6da442497eb4f1a5f2e11f9d7a
```

Then run:
```powershell
streamlit run streamlit_app.py
```

Note: Make sure `python-dotenv` is installed if using .env file.

## Testing Steps

### 1. Start the App

Run one of the methods above. The app should open in your browser at `http://localhost:8501`

### 2. Test Categorization

1. Click "🔄 Artikelen Vernieuwen" in the sidebar
2. Wait for articles to be imported
3. Articles should be automatically categorized using ChatLLM
4. Check the categories in the article cards or detail view

### 3. Test ELI5 Summaries

1. Click on an article to view details
2. Click "✨ Genereer eenvoudige uitleg" button
3. Wait for the summary to generate
4. The summary should appear in an expandable section

Or use the batch generator:
1. Click "✨ Genereer ELI5 samenvattingen" in the sidebar
2. Wait for summaries to be generated
3. Check articles to see the summaries

## Verifying ChatLLM is Working

### Check Console Output

When you import articles or generate summaries, you should see:
- No "ChatLLM API error" messages (if you see errors, it's falling back to other methods)
- Articles being categorized
- ELI5 summaries being generated

### Check Article Categories

1. Import some articles
2. View an article detail
3. Check if it has multiple relevant categories assigned
4. Categories should be more accurate than keyword-based matching

### Check ELI5 Quality

1. Generate an ELI5 summary
2. The summary should:
   - Use simple Dutch words
   - Be 2-3 sentences
   - Explain capitalized words/names if needed
   - Be child-friendly

## Troubleshooting

### "ChatLLM API error" in console

**Possible causes:**
- API endpoint might be different
- API key format might be incorrect
- Network issues

**Solution:**
- The app will automatically fall back to other APIs or keyword matching
- Check the console for specific error messages
- Verify the API key is set correctly: `echo $env:CHATLLM_API_KEY` (PowerShell) or `echo $CHATLLM_API_KEY` (Bash)

### API Key Not Working

**Check:**
1. Verify the key is set: `echo $env:CHATLLM_API_KEY` (Windows) or `echo $CHATLLM_API_KEY` (Mac/Linux)
2. Make sure you're in the same terminal session where you set it
3. Try restarting the Streamlit app

### App Still Using Keyword Matching

If articles are being categorized with keyword matching instead of ChatLLM:

1. **Check API key is set:**
   ```powershell
   # Windows
   $env:CHATLLM_API_KEY
   
   # Mac/Linux
   echo $CHATLLM_API_KEY
   ```

2. **Check console for errors** - ChatLLM might be failing silently and falling back

3. **Try setting it again** in the same terminal session

### Environment Variable Not Persisting

Environment variables set in PowerShell/Bash only last for that session. Options:

1. **Use the test script** - It sets the variable and runs the app in one go
2. **Create .env file** - More permanent solution
3. **Set in your shell profile** - For permanent setup (advanced)

## Expected Behavior

### With ChatLLM Working:
- ✅ Articles get multiple relevant categories
- ✅ ELI5 summaries are high quality and child-friendly
- ✅ Categorization is more accurate than keyword matching
- ✅ No error messages in console

### Without ChatLLM (Fallback):
- ✅ App still works (uses keyword matching)
- ✅ ELI5 summaries use simple extraction
- ⚠️ Less accurate categorization
- ⚠️ Simpler ELI5 summaries

## Next Steps

Once local testing works:
1. **Commit your code** (don't commit the API key!)
2. **Deploy to Streamlit Cloud**
3. **Add the API key to Streamlit secrets** (not in code)
4. **Test in production**

The app is designed to work even if ChatLLM fails, so you can test locally without worrying about breaking anything!


