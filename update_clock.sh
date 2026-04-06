#!/bin/bash

# This is ran by a Cronjob once a day at 5:00 AM 
# to pull any changes from the remote repository

echo Stopping clock.service
sudo systemctl stop clock.service

echo Attempting to pull changes from the remote repo
git pull

echo Restarting the Pi
sudo shutdown -r now