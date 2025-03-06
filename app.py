# imports for time stuff
from datetime import datetime, timedelta, timezone                   # for getting the times
import os
import glob
import random

# Libraries for displaying image on screen 
import sys
import logging
import time
import traceback
from PIL import Image, ImageDraw, ImageFont
import epd7in5_V2               # Waveshare's library for their 7.5 inch screen

class Clock:
    get_time: datetime
    curr_time: str
    quotes: list
    filename: str
    quote_buffer: list

    def __init__(self):
        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'BookQuoteClock/images') # path to .bmp files
        self.libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib') # path to 
        if os.path.exists(self.libdir):
            sys.path.append(self.libdir) # TODO: figure out what this does
        logging.basicConfig(level=logging.DEBUG) 
        self.time = datetime.now()
        self.epd = epd7in5_V2.EPD()

        print('clock obj was made.')

    def get_minute(self) -> int:
        return self.time.minute
    
    def get_hour(self) -> str: 
        return self.time.hour

    def get_time(self, hour: int, minute: int) -> str: # e.g. if it's 1:30 PM, this returns '1330'
        if(minute < 10):
            minute = '0' + str(minute)         # e.g 4 becomes 04
        return str(hour) + str(minute)
    
    def update_time(self) -> datetime:
        self.time = datetime.now()
                                    
    def get_quotes(self, filename) -> list: # return all possible quotes for a given minute. helper function for buffer_quotes
        quotes = []
        filename = 'images/' + filename
        if glob.glob(filename):  # get all quotes for the current time
            quotes = glob.glob(filename)    # stores all quotes for the current time; we will choose a random quote from the list
        return quotes

    # Initializes and/or updates the buffer
    def buffer_quotes(self) -> list:
        print('buffer_quote called')
        self.update_time()
        curr_minute = self.get_minute()
        curr_hour = self.get_hour()
        curr_time = self.get_time(curr_hour, curr_minute)
        if 'quote_buffer' not in locals(): # we need to initialize buffer when the clock is turned on
            quote_buffer = []
            while len(quote_buffer) < 3: 
                quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') # used to find all quotes for a specific time e.g. 'quote_1510_*.bmp'
                filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(quotes))) + '.bmp'        
                quote_buffer.append(filename)

                # get the quotes that will be displayed one and two minutes after current quote
                if(curr_minute == 59): # if we are on the 59th minute of the hour (e.g. 11:59)
                    self.time = self.time.replace(second=0, microsecond=0) + timedelta(minutes=1) + timedelta(hours=1)
                    curr_hour = self.get_hour() # set current hour to next hour
                    curr_minute = self.get_minute() # set current minute to next minute

                else: # we are not on the 59 minute, so we only need to get the next minute
                    self.time = self.time.replace(second=0) + timedelta(minutes=1)
                    curr_minute = self.get_minute()  # set current minute to next minute
                
                curr_time = self.get_time(curr_hour, curr_minute) # update the time
                print(quote_buffer)
        else: # otherwise, our buffer is already initialized, so we only need to buffer the quote that's 2 minutes ahead
            if(curr_minute == 59): 
                self.time = self.time.replace(second=0) + timedelta(hours=1) + timedelta(minutes=2)
                curr_hour = self.get_hour()
                curr_minute = self.get_minute()  # set current minute to 2 minutes ahead

            else: # we are not on the 59th minute, so we don't need the next hour
                self.time = self.time.replace(second=0) + timedelta(minutes=2)
                curr_minute = self.get_minute()
            curr_time = self.get_time(curr_hour, curr_time) # update the time
            quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') # get the list of quotes for the 2-minutes-ahead of current quote
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(quotes))) + '.bmp' # get the .bmp file for the 2-minutes-ahead quote
            quote_buffer.append(filename) # add 2-minutes-ahead quote to buffer
            print('buffer quote finish')
        return quote_buffer

    def display_quote(self, buffer):
        try:
            print('display_quote was called')
            logging.info("Book Quote Clock")
            logging.info('reading .bmp file...')
            filename = buffer.pop(0) # pop the current quote
            quote = Image.open(os.path.join(self.picdir, filename))
            self.epd.display(self.epd.getbuffer(quote))
            time.sleep(2)
            print('display_quote finish')
        except IOError as e:
            logging.info(e)
    

    def main(self):
        """
        use the python crontab library to schedule main to be called once a minute
        in main, we call buffer_quotes and display_quote
        """ 
        print('main was called.')
        quote_buffer = self.buffer_quotes()               # buffer the current quote, and the following two quotes to display
        self.display_quote(quote_buffer)                          # display the current quote
        print('main finish')

if __name__ == '__main__':
    try:
        clock = Clock() 
        clock.epd.init_fast() # initialize the screen
        '''
        We will use current_minute and next_minute to determine how long the program should sleep
        when it is started, because it won't start exactly at the 0th second of a minute; it will 
        start when the Rpi is plugged in and boots up.
        '''
        while True:
            logging.info("Clear...")

            clock.main()
            current_seconds = time.time() # get the number of seconds since the UTC epoch for the current time
            next_minute = datetime.now(timezone.utc) # update the clock's time again just to be safe
            next_minute= next_minute.replace(second=0, microsecond=0) + timedelta(minutes=1) # the next minute
            next_minute = datetime.timestamp(next_minute) # get the number of seconds since the UTC epoch for the next minute
            sleep_time = int(next_minute - current_seconds) # get the difference between the two and sleep (i.e., wait until the next minute to display the next quote)
            print("sleep for: " + str(sleep_time) + " seconds")
            time.sleep(sleep_time) # sleep until next minute

    except KeyboardInterrupt as e:
        logging.info(e)
        epd7in5_V2.EPD.Clear()
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()
