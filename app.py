# imports for time stuff
from datetime import datetime, timedelta                   # for getting the times
import os
import glob
import random
from crontab import CronTab

# Libraries for displaying image on screen 
import sys
import logging
import time
import traceback
from PIL import Image, ImageDraw, ImageFont
#from epd7in5_V2 import *               # Waveshare's library for their 7.5 inch screen

class Clock:

    get_time: datetime
    curr_time: str
    quotes: list
    filename: str
    quote_buffer: list



    def __init__(self):
        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'image') # path to .bmp files
        self.libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib') # path to 
        if os.path.exists(self.libdir):
            sys.path.append(self.libdir) # TODO: figure out what this does
        logging.basicConfig(level=logging.DEBUG) 
        self.time = datetime.now()
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
            print(quote_buffer)
            return quote_buffer

    def display_quote(self, buffer):
        try:
            logging.info("Book Quote Clock")
            #epd = self.epd7in5_V2.EPD()

            logging.info("init and Clear")
            #epd.init()
            #epd.Clear()

            logging.info('reading .bmp file...')
            filename = buffer.pop(0) # pop the current quote
            quote = Image.open(os.path.join(self.picdir, filename))
            #epd.display(epd.getbuffer(quote))
            time.sleep(2)
        except IOError as e:
            logging.info(e)

    def main(self):
        """
        use the python crontab library to schedule main to be called once a minute
        in main, we call buffer_quotes and display_quote
        """ 
        quote_buffer = self.buffer_quotes()               # buffer the current quote, and the following two quotes to display
        self.display_quote(quote_buffer)                          # display the current quote
        
        print('main')

if __name__ == '__main__':
    try:
        cron = CronTab(user = 'username') # TODO: maybe move the cronjob and calling main to a separate file?
        job = cron.new(command = 'python3 app.py')
        clock = Clock()
        clock.main()
    except KeyboardInterrupt as e:
        logging.info(e)
        #clock.epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()