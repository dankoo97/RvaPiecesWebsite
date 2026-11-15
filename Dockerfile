# Stage 1: Builder stage
FROM python:3.13-slim AS builder

# git is needed for dependencies installed from git (e.g. the berserk fork)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency definitions
COPY pyproject.toml uv.lock ./

# Install the exact locked (non-dev) dependencies into the system python
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt

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
