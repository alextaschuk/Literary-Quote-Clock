#!/bin/sh
# Name: Literary Clock
# Author: alextaschuk
# Icon: /mnt/us/literary_clock/thumbnail.jpg
# DontUseFBInk: true

PID_FILE=/tmp/literary_clock.pid
LOG=/tmp/literary_clock.log
#LOG=/mnt/us/literary_clock.log
IMAGES=/mnt/us/literary_clock/images

# adds the fbink binary to the shell path so that
# the shell can find it and use the fbink commands
export PATH=mnt/us/libkh/bin/:$PATH

log() { echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

run_clock() {
    log "Literary Quote Clock Started"

    # Detect display mode once at startup
    if command -v fbink > /dev/null 2>&1; then
        DISPLAY_MODE=fbink
        log "display mode: fbink"
    else
        DISPLAY_MODE=eips
        log "display mode: eips (fbink not found)"
    fi

    if [ "$DISPLAY_MODE" = fbink ]; then
    else
        if [ ! -d "$IMAGES" ]; then
            log "ERROR: images dir not found: $IMAGES"
            return 1
        fi
    fi

    while true; do
        TIME=$(date +"%H:%M")
        TIME_KEY=$(date +"%H%M")
        log "Displaying quote for $TIME"
        
        QUOTE_IMGS=$(ls "${IMAGES}/metadata/quote_${TIME_KEY}_"*.png 2>/dev/null)

        if [ -z "$QUOTE_IMGS" ]; then
            log "($QUOTE_IMGS) no images for $TIME_KEY, sleeping"
            sleep "$((60 - $(date +%S)))"
            continue
        fi

        # choose a random image from QUOTE_IMGS
        IMAGE=$(printf '%s\n' $QUOTE_IMGS | awk '
            BEGIN { srand() }
            { a[++n] = $0 }
            END { print a[int(rand() * n) + 1] }
        ')
        log "image: $IMAGE"

        MINUTE=$(date +"%M")
        if [ "$MINUTE" == "59" ]; then
            eips -c -f >> "$LOG" 2>&1 # perform a full refresh every hour
        else
            eips -c >> "$LOG" 2>&1 # -c = clear screen (partial refresh)
        fi
        eips -g "$IMAGE" >> "$LOG" 2>&1 # -g = show image

        sleep "$((60 - $(date +%S)))"
    done
}

# Toggle: If the clock is already running, kill the process and exit
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    fbink "Stopping the clock..."
    sleep 2
    kill "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
    exit 0
else
    fbink "Starting the clock..."
    sleep 2
fi

# Start clock loop in background
run_clock & echo $! > "$PID_FILE"
