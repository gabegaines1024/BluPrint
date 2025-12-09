# BluPrint Deployment Guide

This guide covers deploying the BluPrint PC Builder application to production.

## Prerequisites

- Python 3.11+
- PostgreSQL (recommended for production) or SQLite (development only)
- Docker and Docker Compose (optional, for containerized deployment)
- Gunicorn (included in requirements)

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required
FLASK_ENV=production
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/bluprint

# Optional
JWT_ACCESS_TOKEN_EXPIRES=86400
LOG_LEVEL=WARNING
LOG_FILE=/var/log/bluprint/app.log
CORS_ORIGINS=https://yourdomain.com
```

### Generating Secret Keys

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database Setup

### PostgreSQL (Recommended for Production)

1. Install PostgreSQL:
```bash
sudo apt-get install postgresql postgresql-contrib
```

2. Create database and user:
```sql
CREATE DATABASE bluprint;
CREATE USER bluprint_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bluprint TO bluprint_user;
```

3. Update `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://bluprint_user:your_password@localhost:5432/bluprint
```

### SQLite (Development Only)

For development, SQLite is used by default. The database file will be created in the `instance/` directory.

## Installation

### Option 1: Docker Deployment (Recommended)

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. Run database migrations:
```bash
docker-compose exec web flask db upgrade
```

3. The application will be available at `http://localhost:5000`

### Option 2: Manual Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install gunicorn
```

2. Set environment variables (see above)

3. Run database migrations:
```bash
export FLASK_APP=run.py
flask db upgrade
```

4. Start the application with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app
```

## Production Server Configuration

### Using Gunicorn

```bash
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  run:app
```

### Using Systemd (Linux)

Create `/etc/systemd/system/bluprint.service`:

```ini
[Unit]
Description=BluPrint PC Builder
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/BluPrint
Environment="PATH=/path/to/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bluprint
sudo systemctl start bluprint
```

### Using Nginx as Reverse Proxy

Create `/etc/nginx/sites-available/bluprint`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/bluprint /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Health Checks

The application includes a health check endpoint at `/health`:

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "database": "healthy"
}
```

## Database Migrations

### Creating a New Migration

```bash
export FLASK_APP=run.py
flask db migrate -m "Description of changes"
```

### Applying Migrations

```bash
flask db upgrade
```

### Rolling Back

```bash
flask db downgrade
```

## Security Considerations

1. **Secret Keys**: Never commit secret keys to version control. Use environment variables.

2. **CORS**: Configure `CORS_ORIGINS` to restrict access to your frontend domain only.

3. **HTTPS**: Use HTTPS in production. Configure SSL certificates with your reverse proxy.

4. **Database**: Use strong passwords for database connections.

5. **Firewall**: Restrict database access to application servers only.

## Monitoring

### Logs

Application logs are written to the location specified in `LOG_FILE` environment variable.

View logs:
```bash
tail -f /var/log/bluprint/app.log
```

### Docker Logs

```bash
docker-compose logs -f web
```

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check database server is running
- Verify user permissions

### Application Won't Start

- Check environment variables are set
- Verify all dependencies are installed
- Check logs for error messages

### 401 Unauthorized Errors

- Verify JWT tokens are being sent in requests
- Check `JWT_SECRET_KEY` matches between restarts
- Verify token hasn't expired

## Backup and Recovery

### Database Backup

PostgreSQL:
```bash
pg_dump -U bluprint_user bluprint > backup.sql
```

SQLite:
```bash
cp instance/bluprint.db backups/bluprint_$(date +%Y%m%d).db
```

### Restore

PostgreSQL:
```bash
psql -U bluprint_user bluprint < backup.sql
```

SQLite:
```bash
cp backups/bluprint_YYYYMMDD.db instance/bluprint.db
```

## Scaling

For high-traffic deployments:

1. Use a load balancer (nginx, HAProxy)
2. Run multiple Gunicorn workers
3. Use a production database (PostgreSQL)
4. Consider Redis for session storage and caching
5. Use a CDN for static assets

## Support

For issues or questions, please refer to the project documentation or open an issue on the repository.

