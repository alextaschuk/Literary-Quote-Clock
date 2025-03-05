# BookQuoteClock

Program to display the time using quotes from various books

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

- Go through Waveshare's example file and get familiar with the code and structure. Figure out what I'll need from it (e.g. any libraries they wrote and/or used), and get my own working test up and running.
- Go through generated images and find quotes that need fixing. use the gremlins extension to find bad characters, such as right quotation, copy it, and find & replace it with a regular quotation. also, use find (cmd + f) `[^\x00-\x7f]` with Regex checked to find bad characters. 
    - One of them is 4:00pm, quote 17 (quote_0400_17). its a stephen king quote with some bad characters
    - another is quote_0430_4. its from cloud atlas
- Combine the list from the original csv with the new one im using to get even more quotes

- Some (possibly) helpful resources at the bottom of Waveshare's documentation:
    - [E-Paper API Analysis](https://www.waveshare.com/wiki/E-Paper_API_Analysis): (Possibly ?) a tutorial/instruction on what is needed to print your own things onto the screen.
    -  [Ink Screen Font Library Tutorial](https://www.waveshare.com/wiki/Ink_Screen_Font_Library_Tutorial): If I want to use other fonts on the screen
    - [Image2Lcd Image Modulo](https://www.waveshare.com/wiki/Image2Lcd_Image_Modulo): Software for converting images to `.bmp` files. All of the exmaple images are in Chinese, so I'm not sure if it will be usable for me.
