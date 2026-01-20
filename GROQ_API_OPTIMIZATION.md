# Groq API Optimalisatie - Minder API Calls

## 📊 Groq Free Tier Limieten

Volgens de Groq documentatie heeft de **Free Tier** de volgende limieten:

- **7.000 requests per dag (RPD)** voor modellen zoals llama-3.1-8b-instant
- **30 requests per minuut (RPM)**
- **500.000 tokens per dag (TPD)**
- **6.000 tokens per minuut (TPM)**

## ⚠️ Het Probleem

Voorheen werd de Groq API **twee keer per artikel** gebruikt:
1. **Categorisatie**: Elke keer dat een artikel werd opgehaald, werd het opnieuw gecategoriseerd met Groq
2. **ELI5 Summary**: Elke keer dat een artikel werd opgehaald, werd er een ELI5 summary gegenereerd

Dit betekende dat als je 100 artikelen had en de RSS checker elke 15 minuten draaide:
- **200 Groq API calls** per check (100 categorisaties + 100 ELI5 summaries)
- Bij 4 checks per uur = **800 calls per uur**
- Bij 24 uur = **19.200 calls per dag** ❌ (veel te veel!)

## ✅ De Oplossing

De code is nu aangepast zodat:

### 1. Categorisatie wordt alleen gedaan voor NIEUWE artikelen
- **Bestaande artikelen** behouden hun bestaande LLM categorisatie
- Alleen als `categorization_llm` is `'Keywords'` of ontbreekt, wordt opnieuw gecategoriseerd
- Dit voorkomt onnodige API calls voor artikelen die al gecategoriseerd zijn

### 2. ELI5 Summary wordt alleen gegenereerd als het ontbreekt
- De functie `generate_missing_eli5_summaries()` haalt alleen artikelen op zonder ELI5
- Bestaande ELI5 summaries worden behouden bij updates
- Dit voorkomt onnodige API calls voor artikelen die al een ELI5 hebben

### 3. Code Wijzigingen

**In `articles_repository.py`:**
- Bij het checken of een artikel bestaat, worden nu ook `categories` en `categorization_llm` opgehaald
- Als een artikel al LLM categorisatie heeft (niet 'Keywords'), wordt deze behouden
- Alleen nieuwe artikelen worden gecategoriseerd met LLM

**In `rss_background_checker.py`:**
- `generate_missing_eli5_summaries()` wordt alleen aangeroepen voor nieuwe artikelen
- Limiet van 10 ELI5 summaries per check om rate limits te voorkomen

## 📈 Nieuwe API Call Schatting

Met de optimalisaties:

### Scenario: 10 nieuwe artikelen per dag
- **Categorisatie**: 10 calls (alleen nieuwe artikelen)
- **ELI5 Summary**: 10 calls (alleen artikelen zonder ELI5)
- **Totaal**: **20 calls per dag** ✅ (binnen de 7.000 limiet!)

### Scenario: 50 nieuwe artikelen per dag
- **Categorisatie**: 50 calls
- **ELI5 Summary**: 50 calls (max 10 per check, maar verspreid over de dag)
- **Totaal**: **~100 calls per dag** ✅ (nog steeds ruim binnen de limiet!)

### Scenario: 100 nieuwe artikelen per dag
- **Categorisatie**: 100 calls
- **ELI5 Summary**: 100 calls (verspreid over meerdere checks)
- **Totaal**: **~200 calls per dag** ✅ (nog steeds ruim binnen de limiet!)

## 🎯 Best Practices

1. **Monitor je API usage** in de Groq Console
2. **Gebruik rate limiting** als je veel artikelen tegelijk verwerkt
3. **Verspreid ELI5 generatie** over meerdere checks (niet alles in één keer)
4. **Gebruik keywords categorisatie** voor artikelen die niet kritisch zijn (sneller, geen API calls)

## 🔧 Aanpassingen in de Code

### Check voor bestaande categorisatie:
```python
# In articles_repository.py, regel ~210
response = storage.client.table('articles').select(
    'id, eli5_summary_nl, categories, categorization_llm, eli5_llm'
).eq('stable_id', article_data['stable_id']).execute()

if response.data and len(response.data) > 0:
    existing = response.data[0]
    # Preserve LLM categorization if it exists
    if existing.get('categorization_llm') and existing.get('categorization_llm') != 'Keywords':
        article_data['categories'] = existing.get('categories', [])
        article_data['categorization_llm'] = existing.get('categorization_llm')
```

### ELI5 wordt al alleen gegenereerd voor ontbrekende:
```python
# In articles_repository.py, regel ~270
def generate_missing_eli5_summaries(limit: int = 5) -> int:
    articles = storage.get_articles_without_eli5(limit=limit)  # Alleen artikelen zonder ELI5
```

## 📝 Conclusie

Met deze optimalisaties zou je **ruim binnen de Groq Free Tier limieten** moeten blijven, zelfs met 100+ nieuwe artikelen per dag. De API wordt nu alleen gebruikt wanneer nodig, niet bij elke RSS check.
