# Categorization Engine Guide

## Overview

The categorization engine automatically categorizes news articles into up to 20 predefined categories using free LLM APIs. Articles can belong to multiple categories.

## Available Categories

1. **binnenland** - Domestic news
2. **Buitenland - Europa** - Foreign news about Europe
3. **buitenland - overig** - Other foreign news
4. **Misdaad** - Crime news
5. **Huizenmarkt** - Housing market news
6. **Economie** - Economic news
7. **bekende Nederlanders** - Famous Dutch people
8. **Nationale Politiek** - National politics
9. **Lokale Politiek** - Local politics
10. **Koningshuis** - Royal family
11. **Technologie** - Technology news
12. **Sport - Voetbal** - Football/soccer
13. **Sport - Wielrennen** - Cycling
14. **overige sport** - Other sports
15. **Internationale conflicten** - International conflicts (e.g., Russia-Ukraine, Israel-Gaza, Sudan)

## How It Works

### 1. LLM-Based Categorization (Primary)

The engine first tries to use free LLM APIs to categorize articles:
- **Groq API** (recommended - fast and free)
- **OpenAI-compatible APIs** (OpenAI, Together AI, etc.)
- **Hugging Face** (fallback)

The LLM analyzes the article title, description, and content to determine which categories apply.

### 2. Keyword-Based Fallback

If LLM APIs are not available or fail, the engine falls back to keyword matching:
- Matches keywords in title, description, and content
- More specific categories are checked first
- Articles can match multiple categories

## Database Schema

### Articles Table
- `categories` (TEXT[] in Supabase, TEXT in SQLite) - Array of category names
- `category` (TEXT) - Legacy single category (kept for compatibility)

### User Preferences Table
- `selected_categories` (TEXT[]) - Categories the user wants to see

## User Preferences

Users can:
1. **Select categories** to include in their personal news feed
2. **Manage blacklist** keywords to hide articles

### Default Behavior
- New users see **all categories** by default
- Users can uncheck categories they don't want to see
- Only articles from selected categories are shown

## Usage

### Automatic Categorization

Articles are automatically categorized when imported from RSS feeds:

```python
from articles_repository import fetch_and_upsert_articles

# Articles are automatically categorized during import
result = fetch_and_upsert_articles(feed_url, max_items=30)
```

### Manual Categorization

```python
from categorization_engine import categorize_article

categories = categorize_article(
    title="Premier bezoekt Oekraïne",
    description="De Nederlandse premier heeft Oekraïne bezocht...",
    content="..."
)
# Returns: ["Buitenland - Europa", "Internationale conflicten", "Nationale Politiek"]
```

### Filtering Articles by Category

```python
# Get articles from specific categories
articles = supabase.get_articles(
    categories=["Sport - Voetbal", "Sport - Wielrennen"],
    limit=50
)
```

## Configuration

### Environment Variables

For LLM-based categorization, set one of:
- `GROQ_API_KEY` - Recommended (fast, free tier)
- `OPENAI_API_KEY` - OpenAI or compatible API
- `HUGGINGFACE_API_KEY` - Hugging Face Inference API

### Without LLM APIs

If no LLM API keys are set, the engine automatically uses keyword-based categorization, which works well for most articles.

## Examples

### Example 1: Multiple Categories

Article: "Premier Rutte bezoekt Oekraïne voor vredesoverleg"

Categories:
- **Buitenland - Europa** (Europe-related)
- **Internationale conflicten** (Ukraine conflict)
- **Nationale Politiek** (Prime Minister Rutte)

### Example 2: Sport Article

Article: "Ajax wint Champions League finale"

Categories:
- **Sport - Voetbal** (Football)
- **binnenland** (Dutch team)

### Example 3: Technology

Article: "Nieuwe AI-wetgeving in Europa"

Categories:
- **Technologie** (AI)
- **Buitenland - Europa** (European legislation)
- **Economie** (may affect tech companies)

## Updating Categories

To add or modify categories:

1. Edit `categorization_engine.py`
2. Update the `CATEGORIES` list
3. Update keyword rules in `_categorize_with_keywords()`
4. Update LLM prompts if needed

## Performance

- **LLM categorization**: ~1-2 seconds per article (with API)
- **Keyword categorization**: <0.01 seconds per article
- **Database storage**: Categories stored as array for efficient filtering

## Troubleshooting

### Articles Not Categorized

- Check if LLM API keys are set correctly
- Verify API quotas/limits
- Check keyword rules match your content

### Wrong Categories

- LLM may misinterpret context
- Keyword rules may need refinement
- Consider adding more specific keywords

### Performance Issues

- Use keyword-based categorization for faster processing
- Limit LLM API calls (use caching)
- Batch categorize articles

