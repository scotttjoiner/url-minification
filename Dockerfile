# Use a lean official Python image
FROM python:3.9-slim

# Don’t buffer stdout/stderr (so logs appear immediately),
# and don’t write .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set a working directory
WORKDIR /app

# Install any OS-level dependencies you need (e.g. for compilation or
# system libraries).  Modify as needed.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
       build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy your dependency file(s) and install
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Ensure Python can import your src/ tree
ENV PYTHONPATH=/app

# Expose the Flask port (Celery doesn't listen on HTTP)
EXPOSE 8888

# Default to running the Flask development server; docker-compose
# will override this for the Celery worker container.
# We assume you’ve set FLASK_APP and FLASK_ENV in your compose file.
CMD ["flask", "run", "--host=0.0.0.0"]