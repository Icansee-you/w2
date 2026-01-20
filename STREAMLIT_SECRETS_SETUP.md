# Streamlit Secrets Setup - Troubleshooting

## Probleem: Supabase connectie werkt niet online

Als je de melding ziet "Testmodus: Gebruikt lokale opslag", betekent dit dat de Supabase connectie niet werkt.

## Oplossing: Controleer Streamlit Secrets

### Stap 1: Ga naar Streamlit Cloud Dashboard
1. Log in op [share.streamlit.io](https://share.streamlit.io)
2. Klik op je app
3. Klik op **⚙️ Settings** (rechtsboven)

### Stap 2: Controleer Secrets
1. Scroll naar **"Secrets"** sectie
2. Klik op **"Edit secrets"**
3. Zorg dat je secrets er zo uitzien:

```toml
[secrets]
SUPABASE_URL = "https://skfizxuvxenrltqdwkha.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrZml6eHV2eGVucmx0cWR3a2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5NTM2OTksImV4cCI6MjA4MTUyOTY5OX0.33ovbBa5MqxXokTPn-RB4C9s7sFG4OaRfl3Zuz0fR6Y"
```

**BELANGRIJK:**
- Gebruik `[secrets]` als header (niet `secrets =`)
- Geen quotes nodig rond de waarden (maar mag wel)
- Geen spaties rond de `=` tekens

### Stap 3: Alternatieve Format (als bovenstaande niet werkt)

Soms werkt het beter met deze format:

```toml
SUPABASE_URL="https://skfizxuvxenrltqdwkha.supabase.co"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrZml6eHV2eGVucmx0cWR3a2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5NTM2OTksImV4cCI6MjA4MTUyOTY5OX0.33ovbBa5MqxXokTPn-RB4C9s7sFG4OaRfl3Zuz0fR6Y"
```

### Stap 4: Save en Herlaad
1. Klik op **"Save"**
2. Wacht tot de app opnieuw deployed is (1-2 minuten)
3. Herlaad de pagina

## Debug: Controleer of Secrets worden gelezen

Als het nog steeds niet werkt, voeg tijdelijk deze code toe aan `streamlit_app.py` (na regel 29):

```python
# DEBUG: Check if secrets are loaded
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        st.write("DEBUG - Secrets object exists")
        if hasattr(st.secrets, 'SUPABASE_URL'):
            st.write(f"DEBUG - SUPABASE_URL found: {st.secrets.SUPABASE_URL[:20]}...")
        else:
            st.write("DEBUG - SUPABASE_URL NOT found in secrets")
    else:
        st.write("DEBUG - No secrets object")
except Exception as e:
    st.write(f"DEBUG - Error: {e}")
```

Verwijder deze debug code weer na het testen!

## Veelvoorkomende Problemen

### Probleem 1: "test@local.com" gebruiker
**Oorzaak:** Lokale opslag wordt gebruikt omdat Supabase niet werkt
**Oplossing:** Fix Supabase secrets (zie boven)

### Probleem 2: Secrets worden niet gelezen
**Oplossing:** 
- Controleer of je `[secrets]` header gebruikt
- Zorg dat er geen typefouten zijn in de key namen
- Gebruik exact: `SUPABASE_URL` en `SUPABASE_ANON_KEY` (hoofdlettergevoelig!)

### Probleem 3: App werkt lokaal maar niet online
**Oorzaak:** Lokaal gebruikt het `.env` bestand, online gebruikt het Streamlit Secrets
**Oplossing:** Zorg dat beide dezelfde waarden hebben

## Test Checklist

- [ ] Secrets zijn toegevoegd in Streamlit Cloud
- [ ] Format is correct (TOML formaat)
- [ ] Geen typefouten in key namen
- [ ] App is opnieuw gedeployed na het toevoegen van secrets
- [ ] Geen "Testmodus" melding meer zichtbaar
- [ ] Gebruiker is "test@hotmail.com" (niet "test@local.com")
