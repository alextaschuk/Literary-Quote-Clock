#!/bin/sh
# Name: Literary Quote Clock
# Author: alextaschuk
# Icon: /mnt/us/documents/literary_clock/thumbnail.jpg
# DontUseFBInk: true

PID_FILE=/tmp/literary_clock.pid
LOG=/tmp/literary_clock.log
IMAGES=/mnt/us/documents/literary_clock/images

START_SLEEP=21:30
END_SLEEP=07:00
IN_ACTIVE_HOURS=0

# adds the fbink binary to the shell path so that
# the shell can find it and use the fbink commands
export PATH=/mnt/us/libkh/bin/:$PATH 

log() { echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

check_active_hours()
{
    # Checks if the current time is within START_SLEEP and END_SLEEP.
    # If it is, return false (outside of active hours). Otherwise,
    # return true.

    # prepend a 1 so that times with leading zeros (e.g., 07:15) aren't
    # read by the shell as octal values
    CURR_TIME=$(( 1$(date +%H%M)))
    START=$(( 1$(printf '%s' "$START_SLEEP" | tr -d :)))
    END=$(( 1$(printf '%s' "$END_SLEEP" | tr -d :)))

    log "CURR_TIME=$CURR_TIME, START=$START, END=$END"
    if [ "$CURR_TIME" -lt "$START" ] && [ "$CURR_TIME" -gt "$END" ]; then
        IN_ACTIVE_HOURS=1 # prevent the Kindle from sleeping
        log "IN_ACTIVE_HOURS set to 1"
    else
        IN_ACTIVE_HOURS=0 # allow the Kindle to sleep
        log "IN_ACTIVE_HOURS set to 0"
    fi
    log "IN_ACTIVE_HOURS=$IN_ACTIVE_HOURS"
}

get_image()
{
    # Selects an image at random for the current time to display.
    QUOTE_IMGS=$(ls "${IMAGES}/quote_${TIME_KEY}_"*.png 2>/dev/null)

    if [ -z "$QUOTE_IMGS" ]; then
        log "($QUOTE_IMGS) no images for $TIME_KEY, sleeping"
        return 1
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

    # check if the Kindle natively supports dark mode.
    # the kindle will be put in dark mode when outside of active hours.
        # epdc = Electronic Paper Display Controller
    EPDC_VALUE=$(lipc-get-prop com.lab126.winmgr epdcMode)
    if [ $? -eq 0 ] && [ -n "$EPDC_VALUE" ]; then
        SUPPORTS_epdcMODE=1
        log "set SUPPORTS_epdcMODE to 1"
    else
        SUPPORTS_epdcMODE=0
        log "set SUPPORTS_epdcMODE to 0"
    fi
    LAST_MODE=""
    log "LAST_MODE=$LAST_MODE"

    while true; do
        TIME=$(date +"%H:%M")
        TIME_KEY=$(date +"%H%M")
        log "Displaying quote for $TIME"

        if ! get_image; then
            SEC=$(date +%S)
            sleep "$((60 - ${SEC#0}))"
        fi

        MINUTE=$(date +"%M")
        if [ "$MINUTE" = "00" ]; then
            show_image "$IMAGE" full # perform full refresh every hour
        else
            show_image "$IMAGE"
        fi

        # prevent the screen from sleeping during active hours
        # if the Kindle's battery level is above 20%.
        log "checking active hours"
        check_active_hours
        BATTERY_LVL=$(lipc-get-prop com.lab126.powerd battLevel 2>>"$LOG")
        [ -z "$BATTERY_LVL" ] && BATTERY_LVL=0 # set to 0 if the lipc call ever fails
        log "battery level is $BATTERY_LVL"

        if [ "$IN_ACTIVE_HOURS" = 1 ] && [ "$BATTERY_LVL" -gt 20 ]; then
            lipc-set-prop com.lab126.powerd preventScreenSaver 1
            DESIRED_MODE=Y8
            log "DESIRED_MODE set to $DESIRED_MODE"
        else
            lipc-set-prop com.lab126.powerd preventScreenSaver 0
            DESIRED_MODE=Y8INV
            log "DESIRED_MODE set to $DESIRED_MODE"
        fi

        # change epdc modes only at the beginning or end of active hours
        if [ "$SUPPORTS_epdcMODE" = 1 ] && [ "$DESIRED_MODE" != "$LAST_MODE" ]; then
            lipc-set-prop com.lab126.winmgr epdcMode "$DESIRED_MODE"
            log "epdcMode set to $DESIRED_MODE"
            LAST_MODE="$DESIRED_MODE"
        fi

        SEC=$(date +%S)
        sleep "$((60 - ${SEC#0}))"
    done
}

# If the clock is already running, kill the process and exit
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    fbink "Stopping the clock..."
    lipc-set-prop com.lab126.powerd preventScreenSaver 0
    kill "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
    exit 0
fi

# Start clock loop in background
run_clock & echo $! > "$PID_FILE"
