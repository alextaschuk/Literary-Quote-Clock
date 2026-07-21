#!/bin/sh
# Name: Literary Quote Clock
# Author: alextaschuk
# Icon: /mnt/us/documents/literary_clock/thumbnail.jpg
# DontUseFBInk: true

readonly PID_FILE=/tmp/literary_clock.pid
readonly LOG=/tmp/literary_clock.log
readonly IMAGES=/mnt/us/documents/literary_clock/images

readonly START_SLEEP=21:30
readonly END_SLEEP=07:00
IN_ACTIVE_HOURS=0

# add the fbink binary to the shell path so that
# the shell can find it and use the fbink commands
export PATH=/mnt/us/libkh/bin/:"$PATH"

log() { echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

check_active_hours() {
  #######################################
  # Checks if the current time is within START_SLEEP and END_SLEEP.
  # IN_ACTIVE_HOURS is updated accordingly.
  # Globals:
  #    START_SLEEP
  #    END_SLEEP
  #    IN_ACTIVE_HOURS
  # Arguments:
  #    None
  #######################################

  # prepend a 1 so that times with leading zeros (e.g. 07:15) aren't
  # read by the shell as octal values
  CURR_TIME=$(( 1$(date +%H%M)))
  START=$(( 1$(printf '%s' "$START_SLEEP" | tr -d :)))
  END=$(( 1$(printf '%s' "$END_SLEEP" | tr -d :)))

  if [ "$CURR_TIME" -lt "$START" ] && [ "$CURR_TIME" -gt "$END" ]; then
      IN_ACTIVE_HOURS=1 # no sleep
  else
      IN_ACTIVE_HOURS=0 # yes sleep
  fi
}

check_battery_level() {
  #######################################
  # Read the Kindle's battery percentage. If the lipc call fails,
  # fall back to 0 rather than stopping the clock.
  # GLOBALS:
  #    BATTERY_LVL
  # Arguments:
  #    None
  BATTERY_LVL=$(lipc-get-prop com.lab126.powerd battLevel 2>>"$LOG")
  [ -z "$BATTERY_LVL" ] && BATTERY_LVL=0
}

get_image() {
  #######################################
  # Get all possible images for the current time, select one at
  # random, and store its filepath.
  # Globals:
  #   IMAGE
  # Returns:
  #   Sets exit status to 1 if no image is found for the current time.
  #   Otherwise, the filepath is stored in IMAGE.
  #######################################
  QUOTE_IMGS=$(ls "${IMAGES}/quote_${TIME_KEY}_"*.png 2>/dev/null)

  if [ -z "$QUOTE_IMGS" ]; then
      log "($QUOTE_IMGS) missing quote for $TIME_KEY"
      return 1
  fi

  IMAGE=$(printf '%s\n' "$QUOTE_IMGS" | awk '
      BEGIN { srand() }
      { a[++n] = $0 }
      END { print a[int(rand() * n) + 1] }
  ')
  log "path to selected image: $IMAGE"
}

show_image() {
  #######################################
  # Clear the screen, then display a quote.
  # Arguments:
      # The filepath of a png image to display.
      # (Optional) "full" to perform a full refresh.
  #######################################
  if [ "$2" = full ]; then
    eips -c -f >> "$LOG" 2>&1 # full refresh
  else
    eips -c >> "$LOG" 2>&1 # partial refresh
  fi
  eips -g "$1" >> "$LOG" 2>&1 # display the image
}

run_clock() {
  #######################################
  # The main loop that the clock runs in. The clock
  # performs two one-time checks: 
  #   1. Does the filepath to the images dir exist?
  #   2. Does the Kindle support dark mode?
  # Then, it runs in a continuous loop to display a
  # new quote once every minute.
  # Globals:
  #   IMAGES
  #   IMAGE
  # Arguments:
  #    None
  #######################################
  log "Literary Quote Clock Started"

  if [ ! -d "$IMAGES" ]; then
      log "ERROR: images dir not found: $IMAGES"
      return 1
  fi

    
  if lipc-get-prop com.lab126.winmgr epdcMode >/dev/null 2>&1; then
      SUPPORTS_epdcMODE=1 # epdc = Electronic Paper Display Controller
      log "Dark mode supported"
  else
      SUPPORTS_epdcMODE=0
      log "Dark mode not supported"
  fi
  CURR_MODE="" 

  while true; do
    TIME=$(date +"%H:%M")
    TIME_KEY=$(date +"%H%M")
    log "Displaying quote for $TIME"

    if ! get_image; then
      eips -c
      SEC=$(date +%S)
      sleep "$((60 - ${SEC#0}))"
    fi

    # perform a full refresh at the top of the hour
    MINUTE=$(date +"%M")
    if [ "$MINUTE" = "00" ]; then
      show_image "$IMAGE" full
    else
      show_image "$IMAGE"
    fi

    # prevent the screen from sleeping during active hours if the
    # Kindle's battery is >20%
    check_active_hours
    check_battery_level

    if [ "$IN_ACTIVE_HOURS" = 1 ] && [ "$BATTERY_LVL" -gt 20 ]; then
      lipc-set-prop com.lab126.powerd preventScreenSaver 1
      DESIRED_MODE=Y8
    else
      lipc-set-prop com.lab126.powerd preventScreenSaver 0
      DESIRED_MODE=Y8INV
    fi

    # change epdc modes only at the beginning or end of active hours
    if [ "$SUPPORTS_epdcMODE" = 1 ] && [ "$DESIRED_MODE" != "$CURR_MODE" ]; then
      lipc-set-prop com.lab126.winmgr epdcMode "$DESIRED_MODE"
      CURR_MODE="$DESIRED_MODE"
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
