# Stage 1: Builder stage
FROM python:3.13-slim AS builder

# Install pipenv
RUN pip install pipenv

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# Copy the Django project  and install dependencies
COPY Pipfile Pipfile.lock ./

# run this command to install all dependencies
RUN pipenv install --system --deploy

# Stage 2
FROM python:3.13-slim

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin/

WORKDIR /app

# Copy the application code
COPY --chown=appuser:appuser . .

# Set environment variables to optimize python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKERIZE_VERSION=v0.9.4

RUN apt-get update \
    && apt-get install -y wget \
    && wget -O - https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz | tar xzf - -C /usr/local/bin \
    && apt-get autoremove -yqq --purge wget && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER appuser

# Expose the Django port
EXPOSE 8080

# Run server and migrate data
ENTRYPOINT ["bash", "docker-entrypoint.sh"]
