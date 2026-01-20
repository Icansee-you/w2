# Deployment Guide - Streamlit Cloud

Deze guide legt uit hoe je de website online zet via Streamlit Cloud en GitHub, zonder dat je geheime keys in de code komen.

## 📋 Stap 1: GitHub Repository Voorbereiden

### 1.1 Maak een GitHub Repository
1. Ga naar [GitHub](https://github.com) en maak een nieuwe repository
2. Geef het een naam (bijv. `nieuws-aggregator`)
3. Maak het **publiek** of **privé** (beide werken)

### 1.2 Upload je Code
```bash
# Initialiseer git (als je dat nog niet hebt gedaan)
git init

# Voeg alle bestanden toe
git add .

# Maak je eerste commit
git commit -m "Initial commit"

# Voeg je GitHub repository toe als remote
git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/JOUW-REPO-NAAM.git

# Push naar GitHub
git push -u origin main
```

**⚠️ BELANGRIJK:** Zorg ervoor dat je `.env` bestand **NIET** wordt geüpload! Het staat al in `.gitignore`, maar controleer dit:

```bash
# Controleer of .env in .gitignore staat
cat .gitignore | grep .env
```

Als je `.env` per ongeluk hebt toegevoegd:
```bash
git rm --cached .env
git commit -m "Remove .env from git"
```

## 🔐 Stap 2: Streamlit Cloud Setup

### 2.1 Maak een Streamlit Cloud Account
1. Ga naar [streamlit.io/cloud](https://streamlit.io/cloud)
2. Log in met je GitHub account
3. Autoriseer Streamlit om toegang te krijgen tot je repositories

### 2.2 Deploy je App
1. Klik op "New app"
2. Selecteer je repository
3. Selecteer de branch (meestal `main`)
4. Stel het main file in: `streamlit_app.py`
5. Klik op "Deploy!"

### 2.3 Configureer Secrets (BELANGRIJK!)

**Dit is waar je je geheime keys veilig opslaat:**

1. In je Streamlit Cloud dashboard, klik op je app
2. Klik op "⚙️ Settings" (rechtsboven)
3. Scroll naar "Secrets"
4. Klik op "Edit secrets"
5. Plak de volgende structuur:

```toml
[secrets]
SUPABASE_URL = "https://skfizxuvxenrltqdwkha.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrZml6eHV2eGVucmx0cWR3a2hhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5NTM2OTksImV4cCI6MjA4MTUyOTY5OX0.33ovbBa5MqxXokTPn-RB4C9s7sFG4OaRfl3Zuz0fR6Y"

# LLM API Keys (voeg toe welke je hebt)
GROQ_API_KEY = "je-groq-api-key-hier"
HUGGINGFACE_API_KEY = "je-huggingface-api-key-hier"
OPENAI_API_KEY = "je-openai-api-key-hier"
OPENAI_BASE_URL = "https://api.openai.com/v1"
CHATLLM_API_KEY = "je-chatllm-api-key-hier"

# Test User Password
TEST_USER_PASSWORD = "test123"
```

6. Klik op "Save"
7. Je app wordt automatisch opnieuw gedeployed met de nieuwe secrets

## ✅ Stap 3: Verificatie

### 3.1 Controleer of alles werkt
1. Wacht tot de deployment klaar is (kan 1-2 minuten duren)
2. Open je app URL (bijv. `https://jouw-app.streamlit.app`)
3. Test of:
   - De website laadt
   - Je kunt inloggen
   - Artikelen worden getoond
   - ELI5 summaries worden gegenereerd

### 3.2 Als er problemen zijn
- **"Could not initialize Supabase"**: Controleer of `SUPABASE_URL` en `SUPABASE_ANON_KEY` correct zijn in Secrets
- **"No API key found"**: Controleer of je LLM API keys correct zijn toegevoegd
- **Deployment faalt**: Controleer de logs in Streamlit Cloud dashboard

## 🔄 Stap 4: Updates Deployen

Wanneer je code wijzigingen maakt:

```bash
# Maak je wijzigingen
# ...

# Commit en push
git add .
git commit -m "Beschrijving van je wijzigingen"
git push
```

Streamlit Cloud detecteert automatisch de push en deployed de nieuwe versie!

## 📝 Belangrijke Notities

### ✅ WEL doen:
- ✅ Gebruik Streamlit Secrets voor alle API keys
- ✅ Gebruik `.env` bestand voor lokale ontwikkeling
- ✅ Zorg dat `.env` in `.gitignore` staat
- ✅ Gebruik `.env.example` als template (zonder echte keys)

### ❌ NIET doen:
- ❌ Plaats NOOIT API keys in je code
- ❌ Commit NOOIT je `.env` bestand
- ❌ Deel NOOIT je secrets publiekelijk
- ❌ Gebruik NOOIT hardcoded keys in Python bestanden

## 🆘 Troubleshooting

### Probleem: "Module not found"
**Oplossing:** Zorg dat alle dependencies in `requirements.txt` staan

### Probleem: "Secrets not found"
**Oplossing:** 
1. Controleer of je secrets correct zijn toegevoegd in Streamlit Cloud
2. Controleer of de namen exact overeenkomen (hoofdlettergevoelig!)

### Probleem: App werkt lokaal maar niet online
**Oplossing:**
1. Controleer de deployment logs in Streamlit Cloud
2. Zorg dat alle secrets zijn toegevoegd
3. Controleer of `requirements.txt` up-to-date is

## 📚 Extra Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [GitHub Documentation](https://docs.github.com/)
