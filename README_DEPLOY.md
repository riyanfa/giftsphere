# Docker Deployment

These steps run the project with Docker Compose on any machine that has Docker installed.

1. Create the environment file:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```env
SECRET_KEY=django-insecure-exam-demo-key-7q3u5z9v2n4p8r1s6t0w
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
POSTGRES_PASSWORD=your-db-password
DATABASE_URL=postgresql://giftsphere:your-db-password@db:5432/giftsphere
```

2. Build and start the containers:

```bash
docker compose up -d --build
```

3. Migrations and static files run automatically when the web container starts.

To run them manually if needed:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

4. Optional: create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

5. Open the app:

```text
http://localhost:8000/admin/
http://localhost:8000/api/products/
```

The root URL `/` may return `404 Not Found` because this project is an API backend.