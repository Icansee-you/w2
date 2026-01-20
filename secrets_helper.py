"""
Helper module to get secrets from Streamlit secrets or environment variables.
Works for both local development (.env file) and production (Streamlit Cloud).
"""
import os

def get_secret(key: str, default: str = None) -> str:
    """
    Get secret from Streamlit secrets (production) or environment variable (local).
    
    Args:
        key: The secret key to retrieve
        default: Default value if secret is not found
    
    Returns:
        The secret value or default
    """
    try:
        # Try Streamlit secrets first (for production on Streamlit Cloud)
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    # Fall back to environment variable (for local development)
    return os.getenv(key, default)
