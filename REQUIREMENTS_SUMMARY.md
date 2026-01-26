# Requirements.txt Samenvatting

## Overzicht van Dependencies

### Core Framework
- **streamlit>=1.28.0** - Web framework voor de applicatie
- **Django==5.0.0** - Web framework (mogelijk voor andere doeleinden)
- **gunicorn==21.2.0** - WSGI HTTP server voor productie

### Database & Storage
- **supabase>=2.0.0** - Supabase client voor database en authenticatie
- **psycopg[binary]>=3.1.0** - PostgreSQL adapter (voor Supabase)
- **dj-database-url==2.1.0** - Database URL parser

### Background Tasks
- **celery==5.3.4** - Distributed task queue
- **redis==5.0.1** - Message broker voor Celery

### RSS & Content
- **feedparser>=6.0.11** - RSS feed parser
- **legacy-cgi>=1.0.0** - Legacy CGI module voor Python 3.13+ compatibiliteit

### LLM APIs
- **groq>=0.4.0** - Groq API client (voor ELI5 generatie)
- **huggingface_hub>=0.20.0** - Hugging Face API client (backup LLM)
- **requests>=2.31.0** - HTTP library (voor RouteLLM en andere API calls)

### Utilities
- **python-dotenv==1.0.0** - Environment variable loader (.env files)
- **python-dateutil>=2.8.2** - Date parsing utilities
- **pytz>=2023.3** - Timezone handling
- **whitenoise==6.6.0** - Static file serving voor Django

## Opmerkingen

1. **Django en Celery**: Deze zijn mogelijk niet nodig voor de Streamlit app. Overweeg te verwijderen als ze niet gebruikt worden.
2. **legacy-cgi**: Alleen nodig voor Python 3.13+ compatibiliteit met feedparser
3. **Alle LLM libraries**: Zijn optioneel - de app werkt met fallbacks als ze niet beschikbaar zijn

## Vereiste Secrets/Environment Variables

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `ROUTELLM_API_KEY` - RouteLLM API key (aanbevolen)
- `GROQ_API_KEY` - Groq API key (optioneel, voor ELI5 fallback)
- `HUGGINGFACE_API_KEY` - Hugging Face API key (optioneel, backup LLM)
- `TEST_USER_PASSWORD` - Test user password (optioneel)
