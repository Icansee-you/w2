# How to Run Streamlit App Locally

## Quick Start (Windows)

1. **Open PowerShell** in the project directory

2. **Run the script:**
   ```powershell
   .\run_streamlit.ps1
   ```

That's it! The script will:
- Activate the virtual environment
- Check/install dependencies
- Run database migrations if needed
- Start Streamlit

## Manual Steps

If you prefer to do it manually:

### Step 1: Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 2: Verify Streamlit is Installed

```bash
python -m streamlit --version
```

If not installed:
```bash
pip install streamlit pytz python-dotenv
```

### Step 3: Run the App

```bash
python -m streamlit run streamlit_app.py
```

Or if streamlit command is available:
```bash
streamlit run streamlit_app.py
```

### Step 4: Open Browser

The app will automatically open at `http://localhost:8501`

If it doesn't open automatically, navigate to that URL manually.

## Common Issues

### "streamlit is not recognized"

**Problem**: Virtual environment is not activated.

**Solution**:
1. Activate venv: `.\venv\Scripts\Activate.ps1`
2. Use: `python -m streamlit run streamlit_app.py` instead of just `streamlit`

### "No module named 'dotenv'"

**Problem**: Dependencies not installed in venv.

**Solution**:
```bash
pip install python-dotenv
```

### "No categories found"

**Problem**: Database not initialized.

**Solution**:
```bash
python manage.py init_categories
```

### "No articles found"

**Problem**: No articles imported yet.

**Solution**:
```bash
python manage.py ingest_nos --max-items 100
```

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the Streamlit server.

## Next Steps

Once the app is running locally and working correctly:
1. Test all features
2. Push to GitHub
3. Deploy to Streamlit Cloud (see STREAMLIT_DEPLOYMENT.md)

