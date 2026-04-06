#!/bin/bash

# This is run by a cron job once a day at 4:00 AM 

#echo Stopping clock.service > /home/clock/Desktop/log.txt
sudo systemctl stop clock.service

#echo Attempting to pull changes from the remote repo >> /home/clock/Desktop/log.txt
git pull

#echo Restarting the Pi >> /home/clock/Desktop/log.txt
sudo shutdown -r now
