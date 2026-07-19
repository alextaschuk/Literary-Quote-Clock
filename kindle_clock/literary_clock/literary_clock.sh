#!/bin/sh
# Name: Literary Quote Clock
# Author: alextaschuk
# Icon: /mnt/us/literary_clock/thumbnail.jpg
# DontUseFBInk: true

PID_FILE=/tmp/literary_clock.pid
LOG=/tmp/literary_clock.log
IMAGES=/mnt/us/literary_clock/images

# adds the fbink binary to the shell path so that
# the shell can find it and use the fbink commands
export PATH=/mnt/us/libkh/bin/:$PATH 

log() { echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

get_image()
{
    # Selects an image at random for the current time to display.
    QUOTE_IMGS=$(ls "${IMAGES}/quote_${TIME_KEY}_"*.png 2>/dev/null)

    if [ -z "$QUOTE_IMGS" ]; then
        log "($QUOTE_IMGS) no images for $TIME_KEY, sleeping"
        sleep "$((60 - $(date +%S)))"
        continue
    fi

    IMAGE=$(printf '%s\n' $QUOTE_IMGS | awk '
        BEGIN { srand() }
        { a[++n] = $0 }
        END { print a[int(rand() * n) + 1] }
    ')
    log "path to selected image: $IMAGE"
}

show_image()
{
    # Display a quote on the screen. At the top of hour, perform a full refresh.
    # Args:
        # IMG: Filepath to the png image to be displayed
        # REFRESH: Pass in "full" to perform a full refresh instead of a partial.
    IMG="$1"
    REFRESH="$2"

    if [ "$REFRESH" = full ]; then
        eips -c -f >> "$LOG" 2>&1 # full refresh
    else
        eips -c >> "$LOG" 2>&1 # partial refresh
    fi
    
    eips -g "$IMG" >> "$LOG" 2>&1 # display the image
}

run_clock()
{
    # The main loop that the clock runs in.
    log "Literary Quote Clock Started"

    if [ ! -d "$IMAGES" ]; then
        log "ERROR: images dir not found: $IMAGES"
        return 1
    fi

    while true; do
        TIME=$(date +"%H:%M")
        TIME_KEY=$(date +"%H%M")
        log "Displaying quote for $TIME"

        get_image

        MINUTE=$(date +"%M")
        if [ "$MINUTE" = "59" ]; then
            show_image "$IMAGE" full # perform full refresh every hour
        else
            show_image "$IMAGE"
        fi

        sleep "$((60 - $(date +%S)))"
    done
}

# If the clock is already running, kill the process and exit
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    fbink "Stopping the clock..."
    sleep 2
    kill "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
    exit 0
fi

# Start clock loop in background
run_clock & echo $! > "$PID_FILE"
