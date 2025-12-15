# Quick Start: Streamlit Deployment

## Local Testing

Before deploying to Streamlit Cloud, test locally:

### Quick Setup (Recommended)

**Windows:**
```powershell
.\setup_local.bat
```

**Mac/Linux:**
```bash
chmod +x setup_local.sh
./setup_local.sh
```

This will automatically:
- Activate/create virtual environment
- Install all dependencies
- Show you next steps

### Manual Setup

If you prefer to set up manually:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you get errors, make sure your virtual environment is activated (you should see `(venv)` in your terminal prompt).

### Step 3: Set Up Environment Variables (Optional)

Create a `.env` file in the project root (if you don't have one):

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Note**: The app will work without `.env` file using default values, but it's recommended for local development.

### Step 4: Initialize Database (if not already done)

```bash
python manage.py migrate
python manage.py init_categories
```

**Optional**: Import some articles for testing:
```bash
python manage.py ingest_nos --max-items 100
```

### Step 5: Run Streamlit App

**IMPORTANT**: Make sure your virtual environment is activated first!

**Option 1: Use the PowerShell script (Easiest - Windows):**
```powershell
.\run_streamlit.ps1
```

**Option 2: Manual activation and run:**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run Streamlit
python -m streamlit run streamlit_app.py
```

**Option 3: Using streamlit command directly (if venv is activated):**
```bash
streamlit run streamlit_app.py
```

The app will automatically open in your browser at `http://localhost:8501`

**Note**: If you get "streamlit is not recognized", make sure:
1. Virtual environment is activated (you should see `(venv)` in your prompt)
2. Streamlit is installed: `pip install streamlit`

### Troubleshooting Local Setup

**Error: "streamlit is not recognized" or "streamlit: The term 'streamlit' is not recognized":**
- **Solution**: Your virtual environment is not activated
- Activate it first: `.\venv\Scripts\Activate.ps1` (Windows PowerShell)
- Then use: `python -m streamlit run streamlit_app.py`
- Or use the provided script: `.\run_streamlit.ps1`

**Error: "No module named 'dotenv'" or similar:**
- Make sure your virtual environment is activated
- Run `pip install python-dotenv` or `pip install -r requirements.txt`

**Error: "ModuleNotFoundError: No module named 'celery'":**
- This should be fixed now, but if it persists, make sure all dependencies are installed
- The app will work even if Celery isn't fully configured (it's optional for Streamlit)

**Error: Database connection issues:**
- Make sure `db.sqlite3` exists or DATABASE_URL is set correctly
- Run `python manage.py migrate` first

**Error: "No categories found":**
- Run `python manage.py init_categories`

**Error: psycopg2-binary installation fails:**
- This is OK for local testing with SQLite
- PostgreSQL is only needed for production deployment
- You can skip it: `pip install streamlit pytz python-dotenv` (without psycopg2)

## Deploy to Streamlit Cloud

1. **Push to GitHub** (see STREAMLIT_DEPLOYMENT.md for details)

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file: `streamlit_app.py`
   - Add secrets (DATABASE_URL, DJANGO_SECRET_KEY, etc.)

3. **Initialize database**:
   - Run `python setup_streamlit_db.py` via Streamlit Cloud console
   - Or run Django commands manually

4. **Import articles** (optional):
   ```bash
   python manage.py ingest_nos --max-items 100
   ```

## Troubleshooting

- **No categories**: Run `python manage.py init_categories`
- **No articles**: Run `python manage.py ingest_nos`
- **Database errors**: Check DATABASE_URL in secrets
- **Import errors**: Ensure all files are committed to GitHub

For detailed instructions, see [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md).


