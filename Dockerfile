FROM python:3.11-slim

# Install system dependencies including git for version tracking
RUN apt-get update && apt-get install -y \
    git \
    curl \
    iputils-ping \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create version file from git (if available)
RUN git rev-parse --short HEAD > version.txt 2>/dev/null || echo "unknown" > version.txt

# Create necessary directories with proper permissions
RUN mkdir -p data logs backups scripts && \
    chmod 755 data logs backups scripts

# Make scripts executable
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Expose health check port
EXPOSE 8080

# Enhanced health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run bot with proper signal handling
CMD ["python", "-u", "src/bot.py"]
