#!/bin/bash

echo "🔧 Manual Update Trigger - $(date)"

UPDATE_REQUEST_FILE="/opt/discord-bot-docker/data/update_request.json"
UPDATE_COMPLETE_FILE="/opt/discord-bot-docker/data/update_completed.json"
PROJECT_DIR="/opt/discord-bot-docker"

if [ -f "$UPDATE_REQUEST_FILE" ]; then
    echo "📋 Update request found!"
    
    # Read the update info
    if command -v jq >/dev/null 2>&1; then
        MODE=$(jq -r '.mode // "standard"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
        CHANNEL_ID=$(jq -r '.channel_id // ""' "$UPDATE_REQUEST_FILE" 2>/dev/null)
        OLD_VERSION=$(jq -r '.current_version // "unknown"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
        REQUESTED_BY=$(jq -r '.requested_by // "unknown"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
    else
        MODE="standard"
        CHANNEL_ID=""
        OLD_VERSION="unknown"
        REQUESTED_BY="unknown"
    fi
    
    echo "🔧 Update mode: $MODE"
    echo "📍 Channel ID: $CHANNEL_ID"
    echo "👤 Requested by: $REQUESTED_BY"
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Remove request file
    rm "$UPDATE_REQUEST_FILE"
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Execute update
    if [ "$MODE" = "nuclear" ]; then
        echo "💥 Executing NUCLEAR update"
        bash ./scripts/docker-update.sh nuclear
    else
        echo "🔄 Executing STANDARD update"  
        bash ./scripts/docker-update.sh
    fi
    
    UPDATE_EXIT_CODE=$?
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Get new version
    cd "$PROJECT_DIR"
    NEW_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Create completion file for bot to detect
    if [ $UPDATE_EXIT_CODE -eq 0 ] && [ -n "$CHANNEL_ID" ]; then
        cat > "$UPDATE_COMPLETE_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "channel_id": "$CHANNEL_ID",
  "old_version": "$OLD_VERSION",
  "new_version": "$NEW_VERSION",
  "mode": "$MODE",
  "duration": "${DURATION}s",
  "requested_by": "$REQUESTED_BY",
  "success": true,
  "completion_time": "$(date '+%Y-%m-%d %H:%M:%S UTC')"
}
EOF
        echo "✅ Update completion notification prepared for channel $CHANNEL_ID"
    elif [ $UPDATE_EXIT_CODE -ne 0 ] && [ -n "$CHANNEL_ID" ]; then
        cat > "$UPDATE_COMPLETE_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "channel_id": "$CHANNEL_ID",
  "old_version": "$OLD_VERSION",
  "new_version": "$NEW_VERSION",
  "mode": "$MODE",
  "duration": "${DURATION}s",
  "requested_by": "$REQUESTED_BY",
  "success": false,
  "error": "Update failed with exit code $UPDATE_EXIT_CODE",
  "completion_time": "$(date '+%Y-%m-%d %H:%M:%S UTC')"
}
EOF
        echo "❌ Update failure notification prepared"
    fi
    
    if [ $UPDATE_EXIT_CODE -eq 0 ]; then
        echo "✅ Manual update completed successfully"
    else
        echo "❌ Manual update failed with exit code: $UPDATE_EXIT_CODE"
    fi
    
else
    echo "❌ No update request found"
fi
