# Literary Quote Clock

A project that uses a [Raspberry PI Zero 2WH](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) and Waveshare's [7.5 inch E-ink display](https://www.waveshare.com/7.5inch-e-paper-hat.htm) to display the time using quotes from various books.

## PI and SSH Info

- From Mac, `ping raspberrypi.local` should return success.

- The Pi's IP address is 10.0.0.94

### To SSH

1. Run `ssh alex@raspberrypi.local`
2. Enter the Pi's password: password

- Note: The Raspberry Pi Zero 2W cannot connect to a 5 Ghz WiF channel; it only works with 2.4 GHz. So, if your router is running both channels on the same SSID, you have two options:
    1. Log into your modem and temporarily disable the 5 GHz channel, allowing the PI to connect only to the 2.4 GHz channel. After it connects, you can re-enable the 5 GHz channel.
        - *Note: You will not have to do this every time you turn the PI on. Once it connects to your WiFi on the 2.4 GHz channel for the first time, it will do so automatically every time moving forward.*
    2. Rename the 2.4 GHz channel to have a different SSID.
        - E.g. `SSID-Name-2_4GHz`

### To Run Waveshare's Screen Test

1. CD to `/Desktop/WaveshareTest/e-paper/RaspberryPi-JetsonNano/python/examples`
2. Run `python3 epd_7in5_V2_test.py`

### TODO

**Documentation**

- How does the clock work?

- How to set up the clock from start to finish
    1. install rpi os
    2. set up ssh
    3. create `.service` file
    4. ...

- venv
- pictures of the clock

**Links**
 
- https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual#Working_With_Raspberry_Pi

- https://www.waveshare.com/wiki/E-Paper_API_Analysis

**TODO**

- Dark mode
- Remote login
- Why does # of quote images not match # of csv rows?
- Improve quote formatting
- Go through CSVs, fix/improve quotes, and combine them
- Special Messages

Tech issues
- At 12AM every even minute will cause a full init
- Maybe update journalctl config to clear once a week if it will cause storage issues
- Implement a check for if the author and book title are longer than threshold, it changes the coordinates the start at


- Pi's localization settings need to be changed every time timezone is changed. Maybe automate this using IP?

How to add a crontab that reboots the PI everyday at 4AM as a workaround for desync issues:

    1. `sudo crontab -e`
    2. `0 4 * * * /usr/sbin/reboot
