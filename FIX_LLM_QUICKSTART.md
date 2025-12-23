# Quick Fix: Enable LLM for Categorization and Summaries

## Problem
The LLM features are not working because no API keys are configured. The app is currently using:
- **Categorization**: Keyword matching (basic, but works)
- **Summaries**: Simple text extraction (first 2 sentences)

## Solution: Set Up Groq API (Recommended - Free & Fast)

### Step 1: Get Your Groq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account (or log in)
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key (starts with `gsk_...`)

### Step 2: Set the API Key

**Option A: For Current Session (Temporary)**
```powershell
.\venv\Scripts\Activate.ps1
$env:GROQ_API_KEY="your_groq_api_key_here"
streamlit run streamlit_app.py
```

**Option B: Create .env File (Permanent)**
1. Create a file named `.env` in the project root
2. Add this line:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. Restart Streamlit

### Step 3: Test It

Run the test script:
```powershell
.\venv\Scripts\Activate.ps1
python test_categorization_llm.py
```

Or test in the app:
1. Click "🔄 Artikelen Vernieuwen" to import articles
2. Articles should be categorized using Groq LLM
3. Click on an article to see ELI5 summary (auto-generated)

## Alternative: Hugging Face API (Also Free)

If you prefer Hugging Face:

1. Sign up at https://huggingface.co/
2. Get API key from https://huggingface.co/settings/tokens
3. Set: `$env:HUGGINGFACE_API_KEY="your_key_here"`

## Verify It's Working

After setting the API key:
- **Categorization**: Articles should show more accurate categories
- **Summaries**: Article detail pages should show "Leg uit alsof ik 5 ben" summaries
- Check the console output - you should see which LLM was used

## Troubleshooting

**"No categories generated"**
- Check API key is set: `echo $env:GROQ_API_KEY`
- Make sure virtual environment is activated
- Check internet connection

**"Summary not generated"**
- API might be rate-limited (free tier has limits)
- Try again after a few seconds
- Check console for error messages

