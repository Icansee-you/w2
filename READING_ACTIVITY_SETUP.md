# Reading Activity Tracking Setup

Dit document beschrijft hoe je reading activity tracking instelt voor gebruikers.

## 📋 Overzicht

Het systeem houdt bij welke artikelen gebruikers hebben geopend en gelezen. Dit gebeurt via een `reading_activity` tabel in Supabase.

## 🗄️ Database Setup

### Stap 1: Maak de tabel in Supabase

1. Ga naar je Supabase dashboard
2. Open de **SQL Editor**
3. Kopieer en plak de inhoud van `reading_activity_schema.sql`
4. Klik op **Run** om de tabel en indexes aan te maken

### Stap 2: Verifieer de tabel

Controleer of de tabel correct is aangemaakt:
- Ga naar **Table Editor** in Supabase
- Je zou de `reading_activity` tabel moeten zien met de volgende kolommen:
  - `id` (UUID, primary key)
  - `user_id` (UUID, foreign key naar auth.users)
  - `article_id` (TEXT, foreign key naar articles)
  - `opened_at` (TIMESTAMPTZ)
  - `last_viewed_at` (TIMESTAMPTZ)
  - `read_duration_seconds` (INTEGER)
  - `is_read` (BOOLEAN)
  - `created_at` (TIMESTAMPTZ)
  - `updated_at` (TIMESTAMPTZ)

## 🔧 Functionaliteit

### Automatisch tracking

Wanneer een gebruiker een artikel opent:
- Er wordt automatisch een record aangemaakt in `reading_activity`
- `opened_at` wordt ingesteld op de huidige tijd
- `last_viewed_at` wordt bijgewerkt bij elke keer dat het artikel wordt bekeken

### Beschikbare methodes

De volgende methodes zijn beschikbaar in `supabase_client.py`:

#### `track_article_opened(user_id, article_id)`
Track wanneer een gebruiker een artikel opent. Wordt automatisch aangeroepen wanneer een artikel wordt bekeken.

#### `mark_article_as_read(user_id, article_id, read_duration_seconds=None)`
Markeer een artikel als gelezen. Optioneel kun je de leesduur in seconden meegeven.

**Voorbeeld gebruik:**
```python
# Markeer artikel als gelezen na 30 seconden
supabase.mark_article_as_read(user_id, article_id, read_duration_seconds=30)
```

#### `get_user_reading_activity(user_id, limit=50, only_read=False)`
Haal alle reading activity op voor een gebruiker.

#### `get_user_read_articles(user_id, limit=50)`
Haal een lijst op van artikel IDs die een gebruiker heeft gelezen.

#### `get_user_opened_articles(user_id, limit=50)`
Haal een lijst op van artikel IDs die een gebruiker heeft geopend (gelezen of niet).

#### `is_article_read_by_user(user_id, article_id)`
Controleer of een specifiek artikel is gelezen door een gebruiker.

#### `get_reading_statistics(user_id)`
Haal statistieken op over het leesgedrag van een gebruiker.

**Retourneert:**
```python
{
    'total_articles_opened': 42,
    'total_articles_read': 35,
    'avg_read_duration_seconds': 45.5,
    'read_percentage': 83.3
}
```

## 💡 Gebruiksvoorbeelden

### Artikelen markeren als "gelezen"

Je kunt artikelen automatisch als gelezen markeren wanneer een gebruiker:
- Een bepaalde tijd op de pagina heeft doorgebracht
- Tot het einde van het artikel heeft gescrolld
- Een "Markeer als gelezen" knop heeft geklikt

**Voorbeeld: Markeer als gelezen knop toevoegen**

Voeg dit toe in `render_article_detail()`:

```python
# Na het artikel content
if st.session_state.user:
    user_id = get_user_id(st.session_state.user)
    if user_id:
        is_read = supabase.is_article_read_by_user(user_id, article_id)
        
        if not is_read:
            if st.button("✓ Markeer als gelezen", use_container_width=True):
                supabase.mark_article_as_read(user_id, article_id)
                st.success("Artikel gemarkeerd als gelezen!")
                st.rerun()
        else:
            st.success("✓ Dit artikel is gemarkeerd als gelezen")
```

### Toon gelezen artikelen

Je kunt een pagina toevoegen die alle gelezen artikelen toont:

```python
def render_read_articles_page():
    """Render pagina met gelezen artikelen."""
    supabase = st.session_state.supabase
    
    if not st.session_state.user:
        st.warning("Je moet ingelogd zijn om je gelezen artikelen te zien.")
        return
    
    user_id = get_user_id(st.session_state.user)
    if not user_id:
        return
    
    st.title("📚 Gelezen Artikelen")
    
    # Haal gelezen artikelen op
    read_article_ids = supabase.get_user_read_articles(user_id, limit=100)
    
    if not read_article_ids:
        st.info("Je hebt nog geen artikelen gelezen.")
        return
    
    # Haal artikel details op
    articles = []
    for article_id in read_article_ids:
        article = supabase.get_article_by_id(article_id)
        if article:
            articles.append(article)
    
    # Toon artikelen
    for article in articles:
        render_article_card(article, supabase)
```

### Statistieken weergeven

```python
# In render_gebruiker_page() of een nieuwe statistieken pagina
if st.session_state.user:
    user_id = get_user_id(st.session_state.user)
    if user_id:
        stats = supabase.get_reading_statistics(user_id)
        
        st.subheader("📊 Lees Statistieken")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Geopend", stats['total_articles_opened'])
        with col2:
            st.metric("Gelezen", stats['total_articles_read'])
        with col3:
            st.metric("Leespercentage", f"{stats['read_percentage']:.1f}%")
```

## 🔒 Beveiliging

De tabel gebruikt Row Level Security (RLS) policies:
- Gebruikers kunnen alleen hun eigen reading activity zien
- Gebruikers kunnen alleen hun eigen reading activity toevoegen/updaten
- Alle queries worden automatisch gefilterd op `auth.uid()`

## 📊 Query Voorbeelden

### Meest gelezen artikelen
```sql
SELECT 
    article_id,
    COUNT(*) as read_count
FROM reading_activity
WHERE is_read = TRUE
GROUP BY article_id
ORDER BY read_count DESC
LIMIT 10;
```

### Gebruikers met meeste gelezen artikelen
```sql
SELECT 
    user_id,
    COUNT(*) as read_count
FROM reading_activity
WHERE is_read = TRUE
GROUP BY user_id
ORDER BY read_count DESC
LIMIT 10;
```

### Recent gelezen artikelen (laatste 24 uur)
```sql
SELECT *
FROM reading_activity
WHERE is_read = TRUE
  AND last_viewed_at > NOW() - INTERVAL '24 hours'
ORDER BY last_viewed_at DESC;
```

## 🚀 Volgende Stappen

1. ✅ Voer het SQL schema uit in Supabase
2. ✅ Test de tracking door artikelen te openen
3. 💡 Voeg optioneel een "Markeer als gelezen" knop toe
4. 💡 Voeg een pagina toe om gelezen artikelen te bekijken
5. 💡 Voeg statistieken toe aan de gebruiker pagina

## ⚠️ Opmerkingen

- De tracking gebeurt automatisch wanneer een gebruiker een artikel opent
- Als de tabel nog niet bestaat, faalt de tracking stilletjes (geen error voor de gebruiker)
- Je kunt later extra velden toevoegen zoals `scroll_depth` of `time_on_page`
