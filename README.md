# NOS Nieuws Aggregator

Een Streamlit applicatie voor het verzamelen, categoriseren en samenvatten van nieuwsartikelen met behulp van AI.

## 🚀 Features

- **RSS Feed Monitoring**: Automatisch nieuwe artikelen ophalen elke 15 minuten
- **AI Categorisatie**: Artikelen automatisch categoriseren met LLM APIs
- **ELI5 Samenvattingen**: Eenvoudige uitleg van complexe artikelen
- **Gepersonaliseerde Filters**: Gebruikers kunnen categorieën en keywords filteren
- **Supabase Integratie**: Veilige authenticatie en data opslag

## 📋 Vereisten

- Python 3.8+
- Supabase account
- (Optioneel) LLM API keys: Groq, Hugging Face, of OpenAI

## 🛠️ Lokale Setup

### 1. Clone de repository
```bash
git clone https://github.com/JOUW-GEBRUIKERSNAAM/JOUW-REPO-NAAM.git
cd w2
```

### 2. Installeer dependencies
```bash
python -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configureer environment variables

Kopieer `.env.example` naar `.env`:
```bash
cp .env.example .env
```

Vul je `.env` bestand in met je eigen keys:
```env
SUPABASE_URL=https://jouw-project.supabase.co
SUPABASE_ANON_KEY=jouw-anon-key
GROQ_API_KEY=jouw-groq-key
# etc.
```

### 4. Run de applicatie
```bash
streamlit run streamlit_app.py
```

## ☁️ Deployment naar Streamlit Cloud

Zie [DEPLOYMENT.md](DEPLOYMENT.md) voor gedetailleerde instructies.

**Kort overzicht:**
1. Push je code naar GitHub
2. Maak een Streamlit Cloud account
3. Deploy je app vanuit GitHub
4. Voeg je secrets toe in Streamlit Cloud (Settings → Secrets)

## 🔐 Secrets Management

### Lokale ontwikkeling
Gebruik een `.env` bestand (staat al in `.gitignore`)

### Productie (Streamlit Cloud)
Gebruik Streamlit Secrets in het dashboard:
- Ga naar je app → Settings → Secrets
- Voeg alle benodigde keys toe in TOML formaat

**⚠️ BELANGRIJK:** Plaats NOOIT API keys in je code of GitHub repository!

## 📁 Project Structuur

```
w2/
├── streamlit_app.py          # Hoofdapplicatie
├── supabase_client.py        # Supabase integratie
├── categorization_engine.py  # AI categorisatie
├── nlp_utils.py              # ELI5 generatie
├── articles_repository.py    # Artikel management
├── rss_background_checker.py # RSS feed monitoring
├── secrets_helper.py         # Secrets management helper
├── requirements.txt          # Python dependencies
├── .env.example              # Template voor environment variables
└── DEPLOYMENT.md            # Deployment instructies
```

## 🧪 Testen

De applicatie ondersteunt een lokale testmodus zonder Supabase:
- Als Supabase credentials ontbreken, wordt automatisch lokale opslag gebruikt
- Perfect voor ontwikkeling en testen

## 📝 Licentie

[Voeg je licentie toe]

## 🤝 Contributie

[Voeg contributie instructies toe]
