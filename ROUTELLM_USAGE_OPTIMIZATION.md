# RouteLLM API Usage Optimization

## Probleem
RouteLLM API werd te vaak gebruikt, ook voor artikelen die al gecategoriseerd waren of al een ELI5 samenvatting hadden.

## Oplossing Geïmplementeerd

### 1. Categorisatie Optimalisatie
**Locatie**: `articles_repository.py` - `fetch_and_upsert_articles()`

**Probleem**: 
- `parse_feed_entry()` werd altijd aangeroepen voor elk artikel uit de RSS feed
- Dit betekende dat RouteLLM werd aangeroepen voor ALLE artikelen, ook bestaande

**Oplossing**:
- Eerst controleren of artikel al bestaat (via `stable_id`) VOORDAT `parse_feed_entry()` wordt aangeroepen
- Alleen als artikel NIEUW is, wordt `parse_feed_entry()` aangeroepen (en dus RouteLLM voor categorisatie)
- Als artikel al bestaat, wordt categorisatie overgeslagen (bespaart RouteLLM API call)

**Code wijziging**:
```python
# Extract published_at first (needed for stable_id)
published_at = extract_published_at(entry)
stable_id = generate_stable_id(entry.get('link', ''), published_at)

# Check if article exists BEFORE parsing/categorizing
existing = check_if_article_exists(stable_id)

if existing is None:
    # NEW article - parse and categorize (calls RouteLLM)
    article_data = parse_feed_entry(entry, ...)
    storage.upsert_article(article_data)
else:
    # EXISTING article - skip categorization (saves RouteLLM API call)
    print(f"[RSS Checker] Article already exists, skipping RouteLLM call")
```

### 2. ELI5 Generatie Optimalisatie
**Locatie**: 
- `articles_repository.py` - `generate_missing_eli5_summaries()`
- `streamlit_app.py` - `ensure_eli5_summary()`

**Huidige implementatie**:
- `generate_missing_eli5_summaries()` gebruikt `get_articles_without_eli5()` die alleen artikelen zonder ELI5 ophaalt ✅
- `ensure_eli5_summary()` controleert eerst `if not article.get('eli5_summary_nl'):` voordat het genereert ✅

**Status**: ELI5 generatie is al geoptimaliseerd - wordt alleen aangeroepen voor artikelen zonder ELI5.

## RouteLLM API Calls Nu

RouteLLM wordt NU alleen gebruikt voor:
1. ✅ **Nieuwe artikelen categoriseren** - alleen als artikel nog niet bestaat in database
2. ✅ **ELI5 samenvattingen genereren** - alleen als artikel nog geen ELI5 heeft

RouteLLM wordt NIET meer gebruikt voor:
1. ✅ **Bestaande artikelen opnieuw categoriseren** - wordt overgeslagen
2. ✅ **Artikelen met ELI5 opnieuw samenvatten** - wordt overgeslagen

## Logging

De volgende log berichten helpen bij monitoring:
- `[RSS Checker] Article {stable_id}... already exists with categorization, skipping RouteLLM call` - Categorisatie overgeslagen
- `[INFO] Article categorized with {llm}: {category}` - Nieuwe categorisatie
- `[RouteLLM] Successfully categorized using model {model}` - RouteLLM gebruikt voor categorisatie
- `[RouteLLM ELI5] Successfully generated ELI5` - RouteLLM gebruikt voor ELI5

## Monitoring

Om RouteLLM API usage te monitoren:
1. Check logs voor `[RouteLLM]` berichten
2. Tel aantal nieuwe artikelen per RSS check (zou moeten matchen met RouteLLM categorisatie calls)
3. Tel aantal artikelen zonder ELI5 (zou moeten matchen met RouteLLM ELI5 calls)

## Verwachte Reductie

Voor een RSS feed check met 50 artikelen waarvan 45 al bestaan:
- **Voor**: 50 RouteLLM categorisatie calls
- **Na**: 5 RouteLLM categorisatie calls (alleen nieuwe artikelen)
- **Reductie**: ~90% minder API calls
