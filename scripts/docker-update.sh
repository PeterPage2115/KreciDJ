#!/bin/bash
set -e

echo "🚀 KreciDJ Auto-Update System"
echo "================================"

# Add nuclear option flag
NUCLEAR_MODE=${1:-"normal"}

if [ "$NUCLEAR_MODE" = "nuclear" ]; then
    echo "💥 NUCLEAR MODE: Complete rebuild"
    docker-compose down
    docker system prune -f
    docker rmi $(docker images | grep discord-bot | awk '{print $3}') 2>/dev/null || true
fi

echo "Container: kreci-dj-bot"
echo "Time: $(date)"
echo ""

# Configuration
CONTAINER_NAME="kreci-dj-bot"
BACKUP_DIR="backups/update_$(date +%Y%m%d_%H%M%S)"
HEALTH_URL="http://localhost:8080/health"

# Function to log with timestamp
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# Create backup
log "💾 Creating backup..."
mkdir -p "$BACKUP_DIR"
if [ -d "data" ]; then
    cp -r data/ "$BACKUP_DIR/" 2>/dev/null || true
fi
if [ -d "logs" ]; then
    cp -r logs/ "$BACKUP_DIR/" 2>/dev/null || true  
fi
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
fi
log "✅ Backup created: $BACKUP_DIR"

# Check for updates
log "🔍 Checking for updates..."
git fetch origin main

LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    log "✅ Already up to date!"
    log "Current version: $(git rev-parse --short HEAD)"
    exit 0
fi

log "📥 Updates found!"
log "Current: $(git rev-parse --short HEAD)"
log "Latest:  $(git rev-parse --short origin/main)"

# Show what's changing
log "📋 Recent changes:"
git log --oneline HEAD..origin/main | head -5

# Pull changes
log "⬇️ Pulling latest changes..."
git reset --hard origin/main

# Update version file
git rev-parse --short HEAD > version.txt
log "📝 Version file updated: $(cat version.txt)"

# Check if Docker Compose is running
if ! docker-compose ps | grep -q "kreci-dj-bot"; then
    log "⚠️ Container not running, starting fresh..."
    docker-compose up -d
    sleep 20
else
    # Rebuild and restart
    log "🔨 Rebuilding container..."
    docker-compose build --no-cache discord-bot
    
    log "🔄 Restarting container..."
    docker-compose down
    docker-compose up -d
fi

# Wait for startup
log "⏳ Waiting for bot to start..."
sleep 25

# Health check with retries
log "🏥 Running health check..."
for i in {1..6}; do
    if curl -f "$HEALTH_URL" >/dev/null 2>&1; then
        log "✅ Update successful! Bot is healthy."
        
        # Show final status
        log "📊 Final status:"
        docker-compose ps
        
        # Cleanup old backups (keep last 5)
        log "🧹 Cleaning up old backups..."
        ls -dt backups/update_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
        
        log "🎉 Update completed successfully!"
        exit 0
    fi
    log "⏳ Health check attempt $i/6..."
    sleep 10
done

log "❌ Health check failed after update!"
log "📋 Recent logs:"
docker-compose logs --tail=20 discord-bot

log "🔄 Attempting rollback to backup..."
# Could add rollback logic here if needed

exit 1