# Start from a small official Python image to reduce the runtime image size.
FROM python:3.12-slim

# Prevent Python from writing .pyc files and keep logs flowing to container output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create a dedicated unprivileged account instead of running the web process as root.
RUN groupadd --system app && useradd --system --gid app --create-home app

# Set the working directory for all following build and runtime commands.
WORKDIR /app

# Install Python dependencies in a separate layer to improve Docker build caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application source files into the image.
COPY app.py .
COPY templates ./templates
COPY static ./static

# Create the data directory and grant ownership to the non-root runtime user.
RUN mkdir -p /data && chown -R app:app /app /data

# Drop root privileges before the container starts.
USER app

# Document the port used by Gunicorn; Kubernetes Service maps traffic to this port.
EXPOSE 5000

# Start Gunicorn with two workers; the Helm chart can override this command if needed.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
