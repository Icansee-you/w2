# Groq API Setup Guide

## Step 1: Get Your Groq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account (or log in if you already have one)
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy your API key (it will look like: `gsk_...`)

## Step 2: Set Up Locally

### Option A: Using .env file (Recommended)
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

### Option B: Set Environment Variable Directly

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

**Windows Command Prompt:**
```cmd
set GROQ_API_KEY=your_groq_api_key_here
```

**Linux/Mac:**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

## Step 3: For Streamlit Cloud Deployment

1. Go to your Streamlit Cloud dashboard
2. Select your app
3. Click **Settings** → **Secrets**
4. Add:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Step 4: Test the Setup

Run the test script:
```powershell
python test_llm_integration.py
```

Or test Groq directly:
```powershell
python test_groq.py
```

## Benefits of Groq

- ✅ **Free tier** with generous limits
- ✅ **Very fast** inference (optimized for speed)
- ✅ **Multiple models** available (Llama, Mixtral, etc.)
- ✅ **Reliable** API with good uptime
- ✅ **Works for both** categorization and ELI5 summaries

## Models Available

The app uses `llama-3.1-8b-instant` by default, which is:
- Fast and efficient
- Good for Dutch language
- Free tier friendly

You can modify the model in:
- `nlp_utils.py` → `_generate_with_groq()` function
- `categorization_engine.py` → `_categorize_with_groq()` function

Other available models:
- `llama-3.1-70b-versatile` (more powerful, slower)
- `mixtral-8x7b-32768` (good for longer context)
- `gemma-7b-it` (alternative option)

