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
    # Try Streamlit secrets first (for production on Streamlit Cloud)
    try:
        import streamlit as st
        # Check if we're in a Streamlit context
        if hasattr(st, 'secrets'):
            # Try to access secrets - handle both dict-like and attribute access
            try:
                if hasattr(st.secrets, key):
                    value = getattr(st.secrets, key)
                    if value:
                        return value
            except:
                pass
            
            # Try dict-like access
            try:
                if isinstance(st.secrets, dict) and key in st.secrets:
                    value = st.secrets[key]
                    if value:
                        return value
            except:
                pass
            
            # Try nested access (st.secrets['secrets'][key])
            try:
                if hasattr(st.secrets, 'secrets') and key in st.secrets.secrets:
                    value = st.secrets.secrets[key]
                    if value:
                        return value
            except:
                pass
    except Exception as e:
        # If streamlit is not available or not initialized, continue to env vars
        pass
    
    # Fall back to environment variable (for local development)
    return os.getenv(key, default)
