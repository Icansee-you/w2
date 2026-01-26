# Authenticatie en Voorkeuren Probleem Analyse

## Problemen Geïdentificeerd

### Probleem 1: Gebruiker wordt niet onthouden
**Locatie**: `streamlit_app.py` regel 1877-1926

**Root Cause**:
1. Bij elke page navigatie wordt `main()` opnieuw uitgevoerd
2. Als `st.session_state.user is None`, wordt geprobeerd de gebruiker op te halen via `get_current_user()`
3. Als `get_current_user()` faalt (geen Supabase sessie), wordt auto-login uitgevoerd
4. Het probleem is dat de Supabase sessie mogelijk niet correct wordt bewaard tussen page navigaties

**Mogelijke oorzaken**:
- Supabase client wordt per sessie gemaakt, maar de authenticatie sessie wordt niet correct bewaard
- `persist_session=True` werkt mogelijk niet correct in Streamlit context
- De Supabase sessie wordt mogelijk gereset bij elke rerun

### Probleem 2: Categorie selecties worden niet onthouden
**Locatie**: `streamlit_app.py` regel 1916-1923

**Root Cause**:
```python
# Ensure test@hotmail.com has all categories selected
from categorization_engine import get_all_categories
all_categories = get_all_categories()
if prefs.get('selected_categories') != all_categories:
    # Update to have all categories selected
    supabase.update_user_preferences(user_id, selected_categories=all_categories)
    # Reload preferences
    st.session_state.preferences = supabase.get_user_preferences(user_id)
```

**Probleem**: 
- Deze code wordt uitgevoerd bij ELKE auto-login (elke rerun als gebruiker test@hotmail.com is)
- Als een gebruiker categorieën deselecteert en opslaat, worden ze bij de volgende rerun automatisch weer teruggezet naar alle categorieën
- Dit overschrijft de gebruikersvoorkeuren

## Oplossingen

### Oplossing 1: Verwijder automatisch terugzetten van categorieën
- Verwijder de logica die voorkeuren automatisch terugzet naar alle categorieën
- Laat gebruikers hun eigen voorkeuren instellen en bewaren

### Oplossing 2: Verbeter sessie beheer
- Zorg dat Supabase sessie correct wordt bewaard tussen page navigaties
- Gebruik `st.session_state` om gebruiker te bewaren, niet alleen Supabase sessie
- Voorkom dat `get_current_user()` faalt door sessie correct te bewaren

### Oplossing 3: Verbeter voorkeuren opslag
- Zorg dat voorkeuren correct worden opgeslagen in database
- Zorg dat voorkeuren correct worden opgehaald bij page navigatie
- Voorkom dat voorkeuren worden overschreven door default waarden
