# Database Access Guide

This guide explains how to access your news articles database and how to connect an external database.

## Current Database Setup

By default, the app uses **SQLite** (`db.sqlite3`), which is a file-based database.

### Accessing SQLite Database Locally

**Option 1: Using Python/Django Shell**
```bash
python manage.py shell
```

Then in the shell:
```python
from apps.news.models import Article, Category

# Count articles
Article.objects.count()

# Get all articles
articles = Article.objects.all()

# Get specific article
article = Article.objects.get(id='your-article-id')

# Filter articles
trump_articles = Article.objects.filter(category__key='TRUMP')
russia_articles = Article.objects.filter(category__key='RUSSIA')

# Export to CSV
import csv
with open('articles.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Category', 'Published', 'Link'])
    for article in Article.objects.all():
        writer.writerow([
            article.title,
            article.category.name if article.category else 'None',
            article.published_at,
            article.link
        ])
```

**Option 2: Using SQLite Browser**
1. Download DB Browser for SQLite: https://sqlitebrowser.org/
2. Open `db.sqlite3` file
3. Browse tables: `news_article`, `news_category`, etc.

**Option 3: Using Command Line**
```bash
sqlite3 db.sqlite3

# Then run SQL queries:
.tables
SELECT COUNT(*) FROM news_article;
SELECT title, category_id FROM news_article LIMIT 10;
```

### Accessing SQLite Database on Streamlit Cloud

**Note**: Streamlit Cloud uses ephemeral storage, so the SQLite database is reset on each deployment. For persistent data, use an external database (see below).

To access the database on Streamlit Cloud:
1. The database file is at `/mount/src/w2/db.sqlite3` in the container
2. You can download it via Streamlit Cloud's file browser (if available)
3. Or use Django management commands via the app's console

## Connecting External Database (PostgreSQL Recommended)

For production and persistent storage, use PostgreSQL. Here's how to set it up:

### Step 1: Set Up PostgreSQL Database

**Free Options:**
- **Supabase**: https://supabase.com (Free tier: 500MB database)
- **ElephantSQL**: https://www.elephantsql.com (Free tier: 20MB database)
- **Railway**: https://railway.app (Free tier: $5 credit/month)
- **Render**: https://render.com (Free tier available)

**Example: Supabase Setup**
1. Sign up at https://supabase.com
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (looks like: `postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`)

### Step 2: Update Requirements.txt

Make sure `psycopg2-binary` is in requirements.txt (it was removed earlier for Python 3.13 compatibility, but we can add a compatible version):

```txt
psycopg2-binary>=2.9.9
```

Or use the newer `psycopg` (recommended for Python 3.13+):
```txt
psycopg[binary]>=3.1.0
```

### Step 3: Configure Database URL

**For Streamlit Cloud:**
1. Go to your app settings
2. Click "Secrets"
3. Add:
```toml
DATABASE_URL = "postgres://user:password@host:port/database"
```

**For Local Development:**
Create/update `.env` file:
```env
DATABASE_URL=postgres://user:password@host:port/database
```

### Step 4: Run Migrations

After setting up the database, run migrations:

**Locally:**
```bash
python manage.py migrate
python manage.py init_categories
```

**On Streamlit Cloud:**
The app will auto-run migrations on first load, or you can add a setup script.

### Step 5: Import Articles

Once connected to PostgreSQL:
```bash
python manage.py ingest_nos --max-items 100
```

## Database Connection String Formats

**PostgreSQL:**
```
postgres://username:password@host:port/database
postgresql://username:password@host:port/database
```

**With SSL (required for most cloud providers):**
```
postgres://username:password@host:port/database?sslmode=require
```

**Example (Supabase):**
```
postgres://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
```

## Accessing External Database

### Using Django Shell (Recommended)

```bash
python manage.py shell
```

```python
from apps.news.models import Article, Category

# Query articles
articles = Article.objects.all()
print(f"Total articles: {articles.count()}")

# Filter by category
trump_articles = Article.objects.filter(category__key='TRUMP')
print(f"Trump articles: {trump_articles.count()}")

# Get latest articles
latest = Article.objects.order_by('-published_at')[:10]
for article in latest:
    print(f"{article.title} - {article.category.name if article.category else 'None'}")
```

### Using Database Management Tools

**pgAdmin** (PostgreSQL):
1. Download: https://www.pgadmin.org/
2. Add server with your connection details
3. Browse tables and run queries

**DBeaver** (Universal):
1. Download: https://dbeaver.io/
2. Create new connection → PostgreSQL
3. Enter connection details
4. Browse database

**Supabase Dashboard:**
- Built-in SQL editor
- Table browser
- Query interface

### Exporting Data

**Export to CSV:**
```python
# In Django shell
import csv
from apps.news.models import Article

with open('articles_export.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Title', 'Category', 'Published', 'Link', 'Summary'])
    for article in Article.objects.all():
        writer.writerow([
            str(article.id),
            article.title,
            article.category.name if article.category else 'None',
            article.published_at.isoformat() if article.published_at else '',
            article.link,
            (article.summary or '')[:200]
        ])
```

**Export to JSON:**
```python
import json
from apps.news.models import Article
from django.core import serializers

data = serializers.serialize('json', Article.objects.all()[:100])
with open('articles.json', 'w', encoding='utf-8') as f:
    f.write(data)
```

## Database Schema

**Main Tables:**
- `news_article` - All news articles
- `news_category` - Article categories
- `feed_ingest_ingestionrun` - RSS feed ingestion history
- `accounts_userprofile` - User preferences (if using user accounts)

**Key Fields in `news_article`:**
- `id` (UUID) - Primary key
- `title` - Article title
- `summary` - Article summary
- `content` - Full article content
- `link` - Original article URL
- `category_id` - Foreign key to category
- `published_at` - Publication date
- `image_url` - Article image URL
- `source_name` - Source (usually 'NOS')
- `created_at` - When added to database
- `updated_at` - Last update time

## Troubleshooting

### Connection Issues

**Error: "could not connect to server"**
- Check database URL is correct
- Verify database allows connections from Streamlit Cloud IPs
- Check firewall settings
- Ensure SSL is enabled if required

**Error: "psycopg2 not found"**
- Add `psycopg2-binary` or `psycopg[binary]` to requirements.txt
- For Python 3.13+, use `psycopg[binary]>=3.1.0`

### Migration Issues

**Error: "relation does not exist"**
- Run migrations: `python manage.py migrate`
- Check database URL is correct

### Data Access Issues

**Articles not showing:**
- Check if articles exist: `Article.objects.count()`
- Verify categories are initialized: `Category.objects.count()`
- Check if ingestion ran: `IngestionRun.objects.all()`

## Best Practices

1. **Use PostgreSQL for Production**: SQLite is fine for development, but PostgreSQL is better for production
2. **Backup Regularly**: Set up automated backups for your database
3. **Use Connection Pooling**: For high traffic, use connection pooling
4. **Monitor Performance**: Use database monitoring tools
5. **Secure Credentials**: Never commit database passwords to Git - use secrets/environment variables

## Quick Reference

**Check database connection:**
```python
from django.db import connection
connection.ensure_connection()
print("Connected!")
```

**Count articles by category:**
```python
from apps.news.models import Article, Category
for category in Category.objects.all():
    count = Article.objects.filter(category=category).count()
    print(f"{category.name}: {count}")
```

**Get latest ingestion status:**
```python
from apps.feed_ingest.models import IngestionRun
latest = IngestionRun.objects.order_by('-started_at').first()
print(f"Last run: {latest.started_at}, Status: {latest.status}, Inserted: {latest.inserted_count}")
```

