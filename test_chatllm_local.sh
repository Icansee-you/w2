#!/bin/bash
# Bash script to test ChatLLM locally (Mac/Linux)
# This sets the environment variable and runs the Streamlit app

echo "Setting up ChatLLM API key for local testing..."

# Set the ChatLLM API key
export CHATLLM_API_KEY="s2_733cff6da442497eb4f1a5f2e11f9d7a"

echo "✓ ChatLLM API key set"
echo ""
echo "Starting Streamlit app..."
echo "The app will open in your browser automatically."
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run Streamlit
streamlit run streamlit_app.py


