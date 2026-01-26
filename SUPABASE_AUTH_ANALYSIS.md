# Supabase Authenticatie Probleem Analyse

## Probleem
Twee mensen vanaf hetzelfde IP maar met verschillende devices worden als dezelfde gebruiker gezien door de website.

## Huidige Implementatie

### 1. Supabase Client Initialisatie
- **Locatie**: `supabase_client.py`
- **Probleem**: De Supabase client wordt **globaal gedeeld** via `get_supabase_client()`
- **Code**:
```python
_supabase_client = None  # Globale variabele

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
```

### 2. Session Persistence
- **Locatie**: `supabase_client.py` regel 45
- **Instelling**: `persist_session=True`
- **Betekenis**: Supabase slaat sessies op in browser localStorage/cookies
- **Probleem**: Als de client instance wordt gedeeld, kunnen verschillende browsers dezelfde sessie zien

### 3. Streamlit Session State
- **Locatie**: `streamlit_app.py` regel 501-508
- **Gebruik**: `st.session_state.user` slaat de huidige gebruiker op
- **Probleem**: Streamlit session state is per browser sessie, maar de Supabase client is gedeeld

### 4. Auto-login Logica
- **Locatie**: `streamlit_app.py` regel 1867-1906
- **Probleem**: 
  - `get_current_user()` haalt gebruiker op uit gedeelde Supabase client
  - Als één device inlogt, kan een ander device vanaf hetzelfde IP dezelfde sessie zien

## Root Cause

Het probleem ontstaat omdat:
1. **Globale Supabase Client**: Alle Streamlit sessies delen dezelfde Supabase client instance
2. **Gedeelde Sessie Storage**: Supabase's `persist_session=True` slaat sessies op, maar als de client wordt gedeeld, kunnen verschillende browsers toegang krijgen tot dezelfde sessie
3. **IP-based Session Sharing**: Als twee devices vanaf hetzelfde IP dezelfde Supabase client gebruiken, kunnen ze dezelfde authenticatie sessie delen

## Oplossingen

### Oplossing 1: Per-Session Supabase Client (Aanbevolen)
**Voordeel**: Elke Streamlit sessie krijgt zijn eigen Supabase client instance
**Nadeel**: Iets meer geheugengebruik

**Implementatie**:
```python
# In streamlit_app.py
def init_supabase():
    """Initialize Supabase client per session."""
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = get_supabase_client()
    return st.session_state.supabase_client
```

**Wijziging in supabase_client.py**:
- Verwijder de globale `_supabase_client` variabele
- Of maak een nieuwe functie `create_supabase_client()` die altijd een nieuwe instance maakt

### Oplossing 2: Disable Session Persistence + Manual Session Management
**Voordeel**: Volledige controle over sessies
**Nadeel**: Moet sessies handmatig beheren

**Implementatie**:
```python
# In supabase_client.py
options = ClientOptions(
    auto_refresh_token=True,
    persist_session=False  # Disable automatic persistence
)
```

**Session Management**:
- Sla access tokens op in `st.session_state` in plaats van browser storage
- Elke Streamlit sessie heeft zijn eigen token

### Oplossing 3: Session Identifier + Isolated Storage
**Voordeel**: Elke sessie heeft unieke identifier
**Nadeel**: Complexere implementatie

**Implementatie**:
```python
# Genereer unieke sessie ID per Streamlit sessie
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Gebruik session_id om Supabase storage te isoleren
# (vereist custom storage adapter)
```

### Oplossing 4: Browser-based Session Isolation (Beste)
**Voordeel**: Gebruikt Supabase's ingebouwde browser isolation
**Nadeel**: Vereist dat Supabase client per browser wordt geïnitialiseerd

**Implementatie**:
- Supabase's `persist_session=True` zou automatisch per-browser moeten werken
- Het probleem is dat de client instance wordt gedeeld
- **Fix**: Maak een nieuwe Supabase client per Streamlit sessie

## Aanbevolen Oplossing

**Oplossing 1 + 4 combineren**: 
- Maak een Supabase client per Streamlit sessie (niet globaal)
- Behoud `persist_session=True` zodat Supabase automatisch per-browser sessies beheert
- Elke browser krijgt zijn eigen Supabase client instance en zijn eigen sessie

## Implementatie Stappen

1. **Wijzig `supabase_client.py`**:
   - Verwijder globale `_supabase_client` variabele
   - Maak `create_supabase_client()` functie die altijd een nieuwe instance maakt

2. **Wijzig `streamlit_app.py`**:
   - Gebruik `st.session_state` om Supabase client per sessie op te slaan
   - Elke Streamlit sessie krijgt zijn eigen client instance

3. **Test**:
   - Open website op twee verschillende devices vanaf hetzelfde IP
   - Log in met verschillende accounts
   - Verifieer dat elke device zijn eigen sessie heeft

## Code Wijzigingen

### supabase_client.py
```python
# Verwijder globale variabele
# _supabase_client = None  # VERWIJDER

def create_supabase_client():
    """Create a new Supabase client instance."""
    return SupabaseClient()

def get_supabase_client():
    """Get Supabase client (creates new instance each time for session isolation)."""
    return create_supabase_client()
```

### streamlit_app.py
```python
def init_supabase():
    """Initialize Supabase client per session."""
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = create_supabase_client()
    return st.session_state.supabase_client
```

## Alternatieve Oplossing (Sneller)

Als je de globale client wilt behouden maar wel sessie isolatie wilt:

```python
# In supabase_client.py
def get_supabase_client():
    """Get Supabase client with session isolation."""
    # Check if we're in a Streamlit context
    try:
        import streamlit as st
        if hasattr(st, 'session_state'):
            # Use session-specific client
            if 'supabase_client_instance' not in st.session_state:
                st.session_state.supabase_client_instance = SupabaseClient()
            return st.session_state.supabase_client_instance
    except:
        pass
    
    # Fallback to global (for non-Streamlit contexts)
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
```
