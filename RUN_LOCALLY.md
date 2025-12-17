# Complete Guide: Running the App Locally

## Step-by-Step Commands

### Step 1: Open PowerShell/Terminal

Navigate to your project directory:
```powershell
cd C:\Users\Chris\Desktop\NEWCO\w2
```

### Step 2: Activate Virtual Environment (if you have one)

**If you already have a virtual environment:**
```powershell
.\venv\Scripts\Activate.ps1
```

**If you don't have a virtual environment yet, create one:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Set ChatLLM API Key

```powershell
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"
```

### Step 5: Run the Streamlit App

```powershell
streamlit run streamlit_app.py
```

The app will automatically open in your browser at `http://localhost:8501`

---

## All Commands in One Block (Copy & Paste)

```powershell
# Navigate to project (if not already there)
cd C:\Users\Chris\Desktop\NEWCO\w2

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Set ChatLLM API key
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

# Run the app
streamlit run streamlit_app.py
```

---

## Alternative: Use the Test Script

Instead of running commands manually, you can use the test script:

```powershell
.\test_chatllm_local.ps1
```

This does everything automatically!

---

## What You'll See

1. **Terminal output:**
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   Network URL: http://192.168.x.x:8501
   ```

2. **Browser opens automatically** showing the NOS News Aggregator

3. **Test features:**
   - Click "🔄 Artikelen Vernieuwen" to import articles
   - Articles will be categorized using ChatLLM
   - Click on an article and generate ELI5 summary

---

## Troubleshooting

### "streamlit: command not found"
```powershell
pip install streamlit
```

### "venv\Scripts\Activate.ps1: cannot be loaded"
Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Module not found" errors
```powershell
pip install -r requirements.txt
```

### API key not working
Verify it's set:
```powershell
echo $env:CHATLLM_API_KEY
```
Should show: `s2_733cff6da442497eb4f1a5f2e11f9d7a`

---

## Stopping the App

Press `Ctrl+C` in the terminal to stop the Streamlit app.

---

## Next Time You Run

Once everything is set up, you only need:

```powershell
.\venv\Scripts\Activate.ps1
$env:CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"
streamlit run streamlit_app.py
```

Or simply:
```powershell
.\test_chatllm_local.ps1
```


