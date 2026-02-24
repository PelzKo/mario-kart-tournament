FROM python:3.12-slim

# Set working directory to where manage.py lives
WORKDIR /app

# Install Python dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django source
COPY src/ .

# Collect static files at build time (whitenoise serves them)
# Use a dummy key — this is only needed for collectstatic, not runtime
RUN DJANGO_SECRET_KEY=build-phase-collectstatic \
    DJANGO_DEBUG=False \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Entrypoint: run migrations then start gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
