# imports for time stuff
from datetime import datetime, timedelta                   # for getting the times
import os
import glob
import random

# Libraries for displaying image on screen 
import sys
import logging
import time
import traceback
from PIL import Image, ImageDraw, ImageFont
from epd7in5_V2 import epd7in5_V2               # Waveshare's library for their 7.5 inch screen


# constants for image displaying 
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'image') # path to .bmp files
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib') # path to 
if os.path.exists(libdir):
    sys.path.append(libdir) # TODO: figure out what this does

logging.basicConfig(level=logging.DEBUG)


def get_time() -> str:
    get_time = datetime.now()                       # get the current time
    hour = str(get_time.hour)
    if(get_time.minute < 10):
        minute = '0' + str(get_time.minute)         # e.g 4 becomes 04
    else:
        minute = get_time.minute 
    curr_time = str(hour) + str(minute)
    return curr_time
                                 
def get_quotes(filename) -> list: # return all possible quotes for a given minute. helper function for buffer_quotes
    
    if glob.glob(filename):  # get all quotes for the current time
        quotes = glob.glob(filename)    # stores all quotes for the current time; we will choose a random quote from the list
    return quotes

# Initializes and/or updates the buffer
def buffer_quotes() -> list:
    curr_time = get_time()
    if 'quote_buffer' not in locals(): # we need to initialize buffer when the clock is turned on
        quote_buffer = []
        while len(quote_buffer) < 3: 
            quotes = get_quotes('quote_' + curr_time + '_*' + '.bmp') # used to find all quotes for a specific time e.g. 'quote_1510_*.bmp'
            filename = 'quote_' + curr_time + '_' + random.randrange(0, len(quotes)) + '.bmp'        
            quote_buffer.append(filename)

            # get the quotes that will be displayed one and two minutes after current quote
            if(minute == '59'): # if we are on the 59th minute of the hour (e.g. 11:59)
                hour = hour.replace(second=0, microsecond=0) # set seconds and microseconds to zero
                hour = hour + timedelta(hours=1) # set current hour to next hour
                minute = minute.replace(second=0, microsecond=0) 
                minute = minute + timedelta(minutes=1) # set current minute to next minute

            else: # we are not on the 59 minute, so we only need to get the next minute
                minute = minute.replace(second=0, microsecond=0) 
                minute = minute + timedelta(minutes=1) # set current minute to next minute
            
            curr_time = str(hour) + str(minute) # update the time
            print(quote_buffer + " this is the quote buffer when initialized")
    else:
        if(minute == '59'): 
            hour = hour.replace(second=0, microsecond=0) 
            hour = hour + timedelta(hours=1)
            minute = minute.replace(second=0, microsecond=0) 
            minute = minute + timedelta(minutes=2) # set current minute to 2 minutes ahead

        else: # we are not on the 59th minute, so we don't need the next hour
            minute = minute.replace(second=0, microsecond=0) 
            minute = minute + timedelta(minutes=2)
        
        curr_time = str(hour) + str(minute) # update the time
        quotes = get_quotes('quote_' + curr_time + '_*' + '.bmp') # get the list of quotes for the 2-minutes-ahead of current quote
        filename = 'quote_' + curr_time + '_' + random.randrange(0, len(quotes)) + '.bmp' # get the .bmp file for the 2-minutes-ahead quote
        quote_buffer.append(filename) # add 2-minutes-ahead quote to buffer
        print(quote_buffer + " this is the quote buffer after initialization")
        return quote_buffer

def display_quote(buffer):
    try:
        logging.info("Book Quote Clock")
        epd = epd7in5_V2.EPD()

        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        logging.info('reading .bmp file...')
        filename = buffer.pop(0) # pop the current quote
        quote = Image.open(os.path.join(picdir, filename))
        epd.display(epd.getbuffer(quote))
        time.sleep(2)
    except IOError as e:
        logging.info(e)

def main():
    """
    use the python crontab library to schedule main to be called once a minute
    in main, we call buffer_quotes and display_quote
    """ 

    quote_buffer = buffer_quotes()               # buffer the current quote, and the following two quotes to display
    display_quote(quote_buffer)                          # display the current quote
    
    print('main')

if __name__ == 'main':
    try:
        quote_buffer = []
        main()
    except KeyboardInterrupt as e:
        logging.info(e)
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()


# TODO: move all of this to a clock.py file and make it a class. In this file, import that class, create an object, and run main()