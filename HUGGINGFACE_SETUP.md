# Hugging Face Inference API Setup Guide

## Step 1: Get Your Hugging Face API Key

1. Go to https://huggingface.co/
2. Sign up for a free account (or log in if you already have one)
3. Click on your profile icon (top right)
4. Go to **Settings** → **Access Tokens**
5. Click **New token**
6. Give it a name (e.g., "News App")
7. Select **Read** permissions (sufficient for Inference API)
8. Click **Generate token**
9. Copy your token (it will look like: `hf_...`)

## Step 2: Set Up Locally

### Option A: Using .env file (Recommended)
Create or update a `.env` file in the project root:
```
HUGGINGFACE_API_KEY=your_huggingface_token_here
```

### Option B: Set Environment Variable Directly

**Windows PowerShell:**
```powershell
$env:HUGGINGFACE_API_KEY="your_huggingface_token_here"
```

**Windows Command Prompt:**
```cmd
set HUGGINGFACE_API_KEY=your_huggingface_token_here
```

**Linux/Mac:**
```bash
export HUGGINGFACE_API_KEY="your_huggingface_token_here"
```

## Step 3: For Streamlit Cloud Deployment

1. Go to your Streamlit Cloud dashboard
2. Select your app
3. Click **Settings** → **Secrets**
4. Add:
   ```
   HUGGINGFACE_API_KEY=your_huggingface_token_here
   ```

## Step 4: Test the Setup

Run the test script:
```powershell
python test_huggingface.py
```

Or test with the full integration:
```powershell
python test_llm_integration.py
```

## Benefits of Hugging Face

- ✅ **Free tier** with generous limits
- ✅ **Many models** available (including Dutch language models)
- ✅ **No credit card** required for basic usage
- ✅ **Reliable** API with good uptime
- ✅ **Works for both** categorization and ELI5 summaries

## Models Used

The app uses these Hugging Face models:

### For ELI5 Summaries:
- `facebook/bart-large-cnn` (English, but works for Dutch)
- `google/flan-t5-base` (multilingual)

### For Categorization:
- `facebook/bart-large-mnli` (zero-shot classification)
- `typeform/distilbert-base-uncased-mnli` (classification)

## Troubleshooting

**"API key not working"**
- Make sure you copied the full token (starts with `hf_`)
- Check that the token has Read permissions
- Verify the token is active in your Hugging Face account

**"Rate limit exceeded"**
- Free tier has rate limits
- Wait a few minutes and try again
- Consider upgrading to a paid plan for higher limits

**"Model not found"**
- Some models may be temporarily unavailable
- The app will fall back to keyword-based categorization
- Check Hugging Face status: https://status.huggingface.co/

## Alternative: Use Local Models

If you want to use models locally (no API needed):
1. Install `transformers` and `torch`:
   ```powershell
   pip install transformers torch
   ```
2. The app can be modified to use local models (requires more setup)

