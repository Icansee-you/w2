# Streamlit Secrets Overzicht

Dit document bevat een overzicht van alle secrets die je moet toevoegen in Streamlit Cloud voor de website om goed te werken.

## 🔐 Verplichte Secrets (Minimaal)

Deze secrets zijn **verplicht** voor de basis functionaliteit:

```toml
[secrets]
# Supabase Database (VERPLICHT)
SUPABASE_URL = "https://jouw-project.supabase.co"
SUPABASE_ANON_KEY = "jouw-anon-key-hier"
```

## 🤖 LLM API Keys (Aanbevolen)

Voor categorisatie en ELI5 samenvattingen heb je minimaal één van deze nodig:

### RouteLLM (Aanbevolen - gebruikt voor categorisatie en ELI5)
```toml
ROUTELLM_API_KEY = "s2_760166137897436c8b1dc5248b05db5a"
```

### Groq (Alternatief - gebruikt voor ELI5 als RouteLLM faalt)
```toml
GROQ_API_KEY = "jouw-groq-api-key-hier"
```

**Let op:** De volgorde is:
1. **Categorisatie**: RouteLLM → Groq → HuggingFace → OpenAI → ChatLLM
2. **ELI5**: Groq → RouteLLM (als beide falen: "failed LLM")

## 📋 Volledige Lijst van Alle Mogelijke Secrets

Als je alle functionaliteit wilt gebruiken, voeg deze toe:

```toml
[secrets]
# VERPLICHT - Supabase Database
SUPABASE_URL = "https://jouw-project.supabase.co"
SUPABASE_ANON_KEY = "jouw-anon-key-hier"

# AANBEVOLEN - LLM voor categorisatie en ELI5
ROUTELLM_API_KEY = "s2_760166137897436c8b1dc5248b05db5a"
GROQ_API_KEY = "jouw-groq-api-key-hier"

# OPTIONEEL - Alternatieve LLM providers (fallback)
HUGGINGFACE_API_KEY = "jouw-huggingface-api-key-hier"
OPENAI_API_KEY = "jouw-openai-api-key-hier"
OPENAI_BASE_URL = "https://api.openai.com/v1"  # Optioneel, default is OpenAI
CHATLLM_API_KEY = "jouw-chatllm-api-key-hier"

# OPTIONEEL - Test gebruiker wachtwoord (voor auto-login)
TEST_USER_PASSWORD = "test123"  # Default, kan worden aangepast
```

## 🎯 Minimale Setup (Aanbevolen)

Voor een werkende website met alle features, voeg minimaal deze toe:

```toml
[secrets]
SUPABASE_URL = "jouw-supabase-url"
SUPABASE_ANON_KEY = "jouw-supabase-anon-key"
ROUTELLM_API_KEY = "s2_760166137897436c8b1dc5248b05db5a"
GROQ_API_KEY = "jouw-groq-api-key"
```

## 📝 Hoe Secrets Toevoegen in Streamlit Cloud

1. Ga naar je Streamlit Cloud dashboard
2. Klik op je app
3. Klik op **⚙️ Settings** (rechtsboven)
4. Scroll naar **"Secrets"**
5. Klik op **"Edit secrets"**
6. Plak de secrets in TOML formaat (zoals hierboven)
7. Klik op **"Save"**

## ⚠️ Belangrijke Opmerkingen

- **SUPABASE_URL** en **SUPABASE_ANON_KEY** zijn **verplicht** - zonder deze werkt de website niet
- **ROUTELLM_API_KEY** is sterk aanbevolen - zonder deze worden artikelen niet goed gecategoriseerd
- **GROQ_API_KEY** is aanbevolen voor ELI5 samenvattingen - zonder deze kunnen ELI5 samenvattingen falen
- Zonder LLM keys worden artikelen gecategoriseerd met "LLM-Failed" en ELI5 toont "failed LLM"
- Alle secrets zijn hoofdlettergevoelig!

## 🔍 Waar Vind Je Deze Keys?

- **Supabase**: Ga naar je Supabase project → Settings → API → Copy URL en anon key
- **RouteLLM**: Je hebt al een key: `s2_760166137897436c8b1dc5248b05db5a`
- **Groq**: Ga naar [console.groq.com](https://console.groq.com) → API Keys → Create API Key
- **HuggingFace**: Ga naar [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → New token
- **OpenAI**: Ga naar [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → Create new secret key

## ✅ Test Checklist

Na het toevoegen van secrets, controleer:

- [ ] Website laadt zonder errors
- [ ] Artikelen worden getoond
- [ ] Artikelen worden gecategoriseerd (check `categorization_llm` in database)
- [ ] ELI5 samenvattingen worden gegenereerd
- [ ] Gebruikers kunnen inloggen
- [ ] RSS feeds worden automatisch gecheckt (elke 15 minuten)
