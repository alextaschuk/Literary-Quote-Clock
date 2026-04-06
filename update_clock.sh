#!/bin/bash

# This is ran by a Cronjob once a day at 4:00 AM 
# to pull any changes from the remote repository

#echo Stopping clock.service > /home/alex/Desktop/log.txt
sudo systemctl stop clock.service

#echo Attempting to pull changes from the remote repo >> /home/alex/Desktop/log.txt
git pull

#echo Restarting the Pi >> /home/alex/Desktop/log.txt
sudo shutdown -r now
