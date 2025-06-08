#!/bin/bash

echo "🔧 Manual Update Trigger - $(date)"

UPDATE_REQUEST_FILE="/opt/discord-bot-docker/data/update_request.json"
PROJECT_DIR="/opt/discord-bot-docker"

if [ -f "$UPDATE_REQUEST_FILE" ]; then
    echo "📋 Update request found!"
    
    # Read the mode
    if command -v jq >/dev/null 2>&1; then
        MODE=$(jq -r '.mode // "standard"' "$UPDATE_REQUEST_FILE" 2>/dev/null)
    else
        MODE="standard"
    fi
    
    echo "🔧 Update mode: $MODE"
    
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
    
    echo "✅ Manual update completed"
else
    echo "❌ No update request found"
fi
