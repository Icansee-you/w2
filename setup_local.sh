#!/bin/bash
# Setup script for Mac/Linux to prepare local Streamlit environment

echo "============================================================"
echo "Streamlit Local Setup"
echo "============================================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "============================================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure virtual environment is activated (you should see (venv) in prompt)"
echo "2. Run: python manage.py migrate"
echo "3. Run: python manage.py init_categories"
echo "4. Run: streamlit run streamlit_app.py"
echo "============================================================"

