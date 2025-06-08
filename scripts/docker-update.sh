#!/bin/bash
set -e

echo "🚀 KreciDJ Auto-Update System v2.0"
echo "=================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/update.log"
BACKUP_DIR="$PROJECT_DIR/backups/auto_$(date +%Y%m%d_%H%M%S)"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
cleanup() {
    log "❌ Update interrupted or failed"
    exit 1
}
trap cleanup INT TERM

# Nuclear mode check
NUCLEAR_MODE=${1:-"normal"}

log "🔍 Starting update process (mode: $NUCLEAR_MODE)"

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Git fetch and check
log "📡 Fetching latest changes..."
timeout 60 git fetch origin main || {
    log "❌ Git fetch timeout"
    exit 1
}

LOCAL_COMMIT=$(git rev-parse --short HEAD)
REMOTE_COMMIT=$(git rev-parse --short origin/main)

log "📊 Current: $LOCAL_COMMIT, Remote: $REMOTE_COMMIT"

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ] && [ "$NUCLEAR_MODE" != "force" ]; then
    log "✅ Already up to date"
    exit 0
fi

# Step 2: Create backup
log "💾 Creating backup..."
mkdir -p "$BACKUP_DIR"
cp -r src/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r data/ "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true
log "✅ Backup created: $BACKUP_DIR"

# Step 3: Pull changes
log "📥 Pulling latest changes..."
timeout 60 git reset --hard origin/main || {
    log "❌ Git pull timeout"
    exit 1
}

# Step 4: Docker operations
log "🐳 Updating Docker container..."

if [ "$NUCLEAR_MODE" = "nuclear" ]; then
    log "💥 Nuclear mode: Complete rebuild"
    timeout 300 docker-compose down || true
    timeout 60 docker system prune -f || true
    timeout 60 docker rmi $(docker images | grep kreci-dj-bot | awk '{print $3}') 2>/dev/null || true
    timeout 600 docker-compose build --no-cache --pull
else
    log "🔄 Standard update"
    timeout 120 docker-compose down
    timeout 300 docker-compose build --no-cache
fi

# Step 5: Start services
log "🚀 Starting services..."
timeout 120 docker-compose up -d

# Step 6: Health check (use external port 9090)
log "🏥 Running health checks..."
sleep 30

# Multiple health check attempts
for i in {1..5}; do
    if curl -f http://localhost:9090/health &>/dev/null; then
        log "✅ Health check passed (attempt $i)"
        break
    else
        log "⚠️ Health check failed (attempt $i/5)"
        if [ $i -eq 5 ]; then
            log "❌ Health check failed after 5 attempts"
            exit 1
        fi
        sleep 10
    fi
done

# Step 7: Update version info
NEW_COMMIT=$(git rev-parse --short HEAD)
echo "$NEW_COMMIT" > version.txt
echo "$(date '+%Y-%m-%d %H:%M:%S') - Updated from $LOCAL_COMMIT to $NEW_COMMIT" >> logs/update_history.log

log "🎉 Update completed successfully!"
log "📍 Version: $LOCAL_COMMIT → $NEW_COMMIT"

exit 0