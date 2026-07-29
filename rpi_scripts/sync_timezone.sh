#!/bin/bash

# This script automatically syncs the PI's timezone.
# It comes from this Stack Exchange comment:  https://raspberrypi.stackexchange.com/a/118629

zone=$(wget -O - -q http://geoip.ubuntu.com/lookup | sed -n -e 's/.*<TimeZone>\(.*\)<\/TimeZone>.*/\1/ p')

if [ "$zone" != "" ]; then
    echo $zone | sudo tee /etc/timezone > /dev/null
    dpkg-reconfigure -f noninteractive tzdata >/dev/null 2>&1
    timedatectl set-timezone $zone
    echo "[INFO] Timezone was set to $zone" >> "$logFile"   
else
    echo "[ERROR] Timezone is empty" >> "$logFile"
fi