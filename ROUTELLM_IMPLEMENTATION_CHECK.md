# RouteLLM Implementatie Check

## Vereisten
1. **Elke 15 minuten** worden RSS feeds gecontroleerd
2. **Alleen NIEUWE artikelen** (die nog niet in Supabase staan) krijgen:
   - Categorisatie via RouteLLM
   - ELI5 samenvatting via RouteLLM/Groq

## Implementatie Status

### ✅ RSS Feed Check Interval
- **Locatie**: `rss_background_checker.py`
- **Interval**: `CHECK_INTERVAL = 15 * 60` (15 minuten = 900 seconden)
- **Status**: ✅ CORRECT geïmplementeerd

### ✅ Alleen Nieuwe Artikelen - Categorisatie
- **Locatie**: `articles_repository.py` - `fetch_and_upsert_articles()`
- **Implementatie**:
  1. Genereert `stable_id` op basis van `link` en `published_at`
  2. **Checkt EERST** of artikel al bestaat in Supabase via `stable_id`
  3. **Alleen als artikel NIEUW is** (`article_is_new = True`):
     - Roept `parse_feed_entry()` aan
     - Dit triggert `categorize_article()` → RouteLLM
  4. **Als artikel al bestaat**:
     - Slaat ALLE processing over (geen RouteLLM call)
     - Logt: `"[RSS Checker] Article ... already exists, skipping ALL processing (no RouteLLM call)"`
- **Status**: ✅ CORRECT geïmplementeerd

### ✅ Alleen Nieuwe Artikelen - ELI5
- **Locatie**: `rss_background_checker.py` - `check_rss_feeds()`
- **Implementatie**:
  1. Na RSS check, alleen als `total_inserted > 0`:
     - Roept `generate_missing_eli5_summaries(limit=min(total_inserted, 10))` aan
  2. `generate_missing_eli5_summaries()`:
     - Roept `storage.get_articles_without_eli5(limit=limit)` aan
     - Deze functie haalt alleen artikelen op waar `eli5_summary_nl IS NULL OR eli5_summary_nl = ''`
  3. **Alleen artikelen zonder ELI5** krijgen een ELI5 samenvatting
- **Status**: ✅ CORRECT geïmplementeerd

### ✅ RouteLLM Counter
- **Categorisatie Counter**: 
  - `categorization_engine.py` - `_routellm_categorization_calls`
  - Verhoogd in `_categorize_with_routellm()` VOOR API call
  - Logt: `"[RouteLLM CATEGORIZATION] API call #X - Categorizing article: ..."`
- **ELI5 Counter**:
  - `nlp_utils.py` - `_routellm_eli5_calls`
  - Verhoogd in `_generate_with_routellm()` VOOR API call
  - Logt: `"[RouteLLM ELI5] API call #X - Generating ELI5 for: ..."`
- **Statistieken**:
  - Na elke RSS check worden counters gelogd in `rss_background_checker.py`
  - Logt: `"[RSS Checker] RouteLLM API calls - Categorization: X, ELI5: Y, Total: Z"`
- **Status**: ✅ CORRECT geïmplementeerd

## Conclusie

✅ **Alle vereisten zijn correct geïmplementeerd:**

1. ✅ RSS feeds worden elke 15 minuten gecontroleerd
2. ✅ Alleen nieuwe artikelen krijgen categorisatie (RouteLLM)
3. ✅ Alleen artikelen zonder ELI5 krijgen een ELI5 samenvatting
4. ✅ RouteLLM API calls worden geteld en gelogd

## RouteLLM API Call Flow

### Voor NIEUWE artikelen:
```
RSS Check (elke 15 min)
  ↓
fetch_and_upsert_articles()
  ↓
Check stable_id → NIEUW artikel
  ↓
parse_feed_entry() → categorize_article() → RouteLLM (Categorisatie) ✅
  ↓
Artikel opgeslagen in Supabase
  ↓
generate_missing_eli5_summaries() → RouteLLM/Groq (ELI5) ✅
```

### Voor BESTAANDE artikelen:
```
RSS Check (elke 15 min)
  ↓
fetch_and_upsert_articles()
  ↓
Check stable_id → BESTAAND artikel
  ↓
SKIP ALLE processing (geen RouteLLM call) ✅
```

## Monitoring

Om RouteLLM usage te monitoren:
1. Check logs voor `[RouteLLM CATEGORIZATION]` en `[RouteLLM ELI5]` berichten
2. Check `[RSS Checker] RouteLLM API calls` statistieken na elke RSS check
3. Tel aantal nieuwe artikelen per check (zou moeten matchen met categorisatie calls)
4. Tel aantal artikelen zonder ELI5 (zou moeten matchen met ELI5 calls)
