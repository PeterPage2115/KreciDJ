#!/bin/bash

# Signal handling for clean shutdown
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🛑 Update Monitor shutting down gracefully"
    exit 0
}

trap cleanup SIGTERM SIGINT

echo "🔍 KreciDJ Update Monitor Started - $(date)"
echo "Monitoring: /opt/discord-bot-docker/data/update_request.json"

UPDATE_REQUEST_FILE="/opt/discord-bot-docker/data/update_request.json"
LOG_FILE="/opt/discord-bot-docker/logs/update-monitor.log"
PROJECT_DIR="/opt/discord-bot-docker"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Update Monitor Started (PID: $$)"

while true; do
    if [ -f "$UPDATE_REQUEST_FILE" ]; then
        log "🚨 Update request detected!"
        
        # Read update info
        if command -v jq >/dev/null 2>&1; then
            MODE=$(jq -r '.mode // "standard"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
            REQUESTED_BY=$(jq -r '.requested_by // "unknown"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
            TARGET_VERSION=$(jq -r '.target_version // "unknown"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
        else
            # Fallback without jq
            MODE=$(grep -o '"mode":"[^"]*"' "$UPDATE_REQUEST_FILE" | cut -d'"' -f4 2>/dev/null)
            REQUESTED_BY=$(grep -o '"requested_by":"[^"]*"' "$UPDATE_REQUEST_FILE" | cut -d'"' -f4 2>/dev/null)
            TARGET_VERSION=$(grep -o '"target_version":"[^"]*"' "$UPDATE_REQUEST_FILE" | cut -d'"' -f4 2>/dev/null)
            
            # Set defaults if empty
            MODE=${MODE:-"standard"}
            REQUESTED_BY=${REQUESTED_BY:-"unknown"}
            TARGET_VERSION=${TARGET_VERSION:-"unknown"}
        fi
        
        log "📝 Update Details:"
        log "   Mode: $MODE"
        log "   Requested by: $REQUESTED_BY" 
        log "   Target version: $TARGET_VERSION"
        
        # Remove the request file to prevent duplicate processing
        rm "$UPDATE_REQUEST_FILE"
        log "🗑️ Update request file removed"
        
        # Change to project directory
        cd "$PROJECT_DIR"
        
        # Make sure script is executable
        chmod +x ./scripts/docker-update.sh
        
        # Execute update
        if [ "$MODE" = "nuclear" ]; then
            log "💥 Executing NUCLEAR update"
            timeout 900 bash ./scripts/docker-update.sh nuclear 2>&1 | tee -a "$LOG_FILE"
        else
            log "🔄 Executing STANDARD update"
            timeout 600 bash ./scripts/docker-update.sh 2>&1 | tee -a "$LOG_FILE"
        fi
        
        UPDATE_EXIT_CODE=$?
        
        if [ $UPDATE_EXIT_CODE -eq 0 ]; then
            log "✅ Update process completed successfully"
        else
            log "❌ Update process failed with exit code: $UPDATE_EXIT_CODE"
        fi
        
        log "📊 Update cycle finished"
        
    fi
    
    # Check every 10 seconds, but make it interruptible
    sleep 10 &
    wait $!
done
