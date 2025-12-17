# Deployment Guide

This guide will help you deploy your Django news aggregator to an external web server.

## Yes, you can deploy this website!

Your project is already configured for deployment with:
- ✅ Production-ready WSGI server (Gunicorn)
- ✅ Static files handling (WhiteNoise)
- ✅ Environment-based configuration
- ✅ PostgreSQL support
- ✅ Docker support (optional)

## Files You Need to Change/Configure

### 1. `.env` File (REQUIRED)

Create or update your `.env` file with production settings. Copy from `.env.example`:

```bash
cp .env.example .env
```

Then edit `.env` with these production values:

```env
# CRITICAL: Change this to a strong random secret key
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here

# CRITICAL: Set to False in production
DEBUG=False

# CRITICAL: Add your domain name(s)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database - Use PostgreSQL in production
DATABASE_URL=postgres://username:password@host:5432/dbname

# Redis - Your Redis server URL
REDIS_URL=redis://your-redis-host:6379/0
```

**How to generate a secret key:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. `config/settings.py` (OPTIONAL - Already Configured)

The settings file is already set up to read from environment variables, so you typically don't need to change it. However, verify these settings:

- ✅ `DEBUG` reads from `DEBUG` env var
- ✅ `ALLOWED_HOSTS` reads from `ALLOWED_HOSTS` env var
- ✅ `SECRET_KEY` reads from `DJANGO_SECRET_KEY` env var
- ✅ Database uses `DATABASE_URL` if set
- ✅ Static files configured with WhiteNoise

## Deployment Steps

### Option 1: Traditional Server Deployment (VPS/Cloud Server)

#### Prerequisites
- Python 3.12+
- PostgreSQL database
- Redis server
- Nginx or Apache (as reverse proxy)

#### Steps:

1. **Upload your code to the server**
   ```bash
   # Using git
   git clone <your-repo-url>
   cd w2
   
   # Or upload via FTP/SFTP
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Initialize categories**
   ```bash
   python manage.py init_categories
   ```

7. **Create superuser** (if needed)
   ```bash
   python manage.py createsuperuser
   ```

8. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

9. **Set up systemd services** (for Gunicorn, Celery)

   Create `/etc/systemd/system/news-aggregator.service`:
   ```ini
   [Unit]
   Description=News Aggregator Gunicorn daemon
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/w2
   Environment="PATH=/path/to/w2/venv/bin"
   ExecStart=/path/to/w2/venv/bin/gunicorn \
       --workers 3 \
       --bind unix:/path/to/w2/news_aggregator.sock \
       config.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/celery-worker.service`:
   ```ini
   [Unit]
   Description=Celery Worker
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/w2
   Environment="PATH=/path/to/w2/venv/bin"
   ExecStart=/path/to/w2/venv/bin/celery -A config worker --loglevel=info

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/celery-beat.service`:
   ```ini
   [Unit]
   Description=Celery Beat
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/w2
   Environment="PATH=/path/to/w2/venv/bin"
   ExecStart=/path/to/w2/venv/bin/celery -A config beat --loglevel=info

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start services:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable news-aggregator celery-worker celery-beat
   sudo systemctl start news-aggregator celery-worker celery-beat
   ```

10. **Configure Nginx** (reverse proxy)

    Create `/etc/nginx/sites-available/news-aggregator`:
    ```nginx
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        location /static/ {
            alias /path/to/w2/staticfiles/;
        }

        location /media/ {
            alias /path/to/w2/media/;
        }

        location / {
            proxy_pass http://unix:/path/to/w2/news_aggregator.sock;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

    Enable site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/news-aggregator /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    ```

11. **Set up SSL with Let's Encrypt** (recommended)
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    ```

### Option 2: Docker Deployment

If your server supports Docker:

1. **Update `.env` file** with production values

2. **Update `docker-compose.yml`** if needed (database credentials, etc.)

3. **Build and start**
   ```bash
   docker-compose up -d --build
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py init_categories
   ```

5. **Set up reverse proxy** (Nginx) to point to `localhost:8000`

### Option 3: Platform-as-a-Service (PaaS)

#### Heroku
1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   worker: celery -A config worker --loglevel=info
   beat: celery -A config beat --loglevel=info
   ```
3. Set environment variables in Heroku dashboard
4. Deploy: `git push heroku main`

#### Railway, Render, DigitalOcean App Platform
- Similar to Heroku
- Set environment variables in platform dashboard
- Connect your Git repository

## Security Checklist

Before going live, ensure:

- [ ] `DEBUG=False` in `.env`
- [ ] Strong `DJANGO_SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Using PostgreSQL (not SQLite) in production
- [ ] HTTPS/SSL configured
- [ ] Database credentials are secure
- [ ] Redis is password-protected (if exposed)
- [ ] Static files are served correctly
- [ ] Media files directory has proper permissions
- [ ] Firewall configured (only ports 80, 443 open)

## Post-Deployment

1. **Test the site** - Visit your domain and verify:
   - Homepage loads
   - Registration/login works
   - Static files (CSS/JS) load
   - Admin panel accessible

2. **Monitor logs**
   ```bash
   # Gunicorn logs
   sudo journalctl -u news-aggregator -f
   
   # Celery logs
   sudo journalctl -u celery-worker -f
   sudo journalctl -u celery-beat -f
   ```

3. **Set up backups** for:
   - Database (PostgreSQL)
   - Media files
   - Environment variables

4. **Monitor performance** and adjust Gunicorn workers if needed

## Troubleshooting

### Static files not loading
- Run `python manage.py collectstatic --noinput`
- Check Nginx configuration for `/static/` location
- Verify `STATIC_ROOT` path in settings

### Database connection errors
- Verify `DATABASE_URL` format
- Check PostgreSQL is running and accessible
- Verify database credentials

### Celery tasks not running
- Check Redis is running: `redis-cli ping`
- Verify `REDIS_URL` in `.env`
- Check Celery worker logs

### 500 errors
- Check `DEBUG=False` is set (won't show detailed errors)
- Check server logs: `sudo journalctl -u news-aggregator -n 50`
- Temporarily set `DEBUG=True` to see error details (remove after fixing!)

## Need Help?

- Check Django logs: `sudo journalctl -u news-aggregator -f`
- Check Celery logs: `sudo journalctl -u celery-worker -f`
- Django documentation: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Gunicorn documentation: https://docs.gunicorn.org/







