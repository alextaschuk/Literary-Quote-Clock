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

logging.basicConfig(level=logging.DEBUG) 

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
        self.time = datetime.now()
        self.quote_buffer = []
        self.quotes = []
        self.epd = epd7in5_V2.EPD()

        print('clock obj was made.')

    def get_minute(self) -> int:
        '''
        Returns the current minute as an integer
            - For example, at 1:30 PM, 30 is returned
        '''
        return self.time.minute
    
    def get_hour(self) -> int:
        '''
        Returns the current hour as an integer
            - For example, at 1:30 PM, 13 is returned
            - For example, at 1:30 AM, 01 is returned
        ''' 
        return self.time.hour

    def get_time(self, hour: int, minute: int) -> str: # e.g. if it's 1:30 PM, this returns '1330'
        '''
        Returns the current time as a string in the 24-hour format.
            - For example, if the current time is 1:30 PM, '1330' is returned.
        '''
        if(minute < 10):
            minute = '0' + str(minute)
        if hour < 10: # if it is midnight, get_hour() returns 0, so we need to append another 0 to have '00'
            hour = '0' + str(hour)
        return str(hour) + str(minute)
    
    def update_time(self) -> datetime:
        '''
        Updates the object's time (an instance of datetime) variable
        ''' 
        self.time = datetime.now()
        return self.time
                                    
    def get_quotes(self, filename) -> list: 
        '''
        A helper function for buffer_quotes that returns all possible quotes for a given minute.
        Returns a list of all filepaths for a given minute.
        '''
        filename = 'images/' + filename
        if glob.glob(filename):                 # get all quotes for the current time
            self.quotes = glob.glob(filename)   # stores all quotes for the current time; we will choose a random quote from the list
        return self.quotes
    
    def init_buffer(self) -> list:
        '''
        Initializes the buffer with the first 3 quotes.
        The first element in the buffer will be the quote for the current time (e.g., 9:40)
        The second element in the buffer will be the quote for the time in one minute (9:41)
        The third element in the buffer will be the quote for the time in two minutes (9:42)

        Returns a list of three Image objects
        '''
        logging.info('init_buffer called. Initializing quote_buffer...')

        self.time = self.update_time()
        curr_minute = self.get_minute()
        curr_hour = self.get_hour()
        curr_time = self.get_time(curr_hour, curr_minute)
        logging.info(f"time: {str(self.time)} curr_minute: {curr_minute} curr_hour: {curr_hour} curr_time: {curr_time}")

        while len(self.quote_buffer) < 3: 
            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') # used to find all quotes for a specific time e.g. 'quote_1510_*.bmp'
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp'

            # this try-except solution is not the best (e.g. wont work if the first quote during init doesn't exist) but it
            # is a short-term soultion for the meantime until I manually go through every time and make sure none are missing.
            try:   
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
            logging.info(f'The filename for the quote being added during intialization: {filename}')     

            # get the quotes that will be displayed one and two minutes after current quote
            if(curr_minute == 59): # if it's the 59th minute of the hour (e.g. 11:59)
                self.time = self.time.replace(minute=0,second=0, microsecond=0) + timedelta(hours=1) # set the time to the next hour (e.g. 12:00)
                curr_hour = self.get_hour() # set current hour to next hour
                curr_minute = self.get_minute() # set current minute to next minute (00)
            else: # it is not the 59 minute, so we only need the next minute
                self.time = self.time.replace(second=0) + timedelta(minutes=1) # set the time to one minute from now
                curr_minute = self.get_minute()  # set current minute to next minute
            curr_time = self.get_time(curr_hour, curr_minute) # update the time

        logging.info(f'init_buffer finish.\n')
        return self.quote_buffer
    
    def update_buffer(self) -> list:
        '''
        To update the buffer, we need to add the quote that's 2 minutes ahead of the currently displayed quote.  
        Because the next quote to be added is 3 minutes ahead of the current quote that is being removed, we 
        add 3 minutes rather than 2 to get the new quote. Due to this logic, we need to check if the current 
        minute is 57,58, or 59 because the hour also needs to get updated when this is the case. 

        Returns an updated list of three Image objects
        
        '''
        logging.info('updating quote_buffer...')

        self.time = self.update_time()
        curr_minute = self.get_minute()
        curr_hour = self.get_hour()
        curr_time = self.get_time(curr_hour, curr_minute)
        logging.info(f"time:{str(self.time)} curr_minute:{curr_minute} curr_hour:{curr_hour} curr_time:{curr_time}")

        if curr_minute + 3 == 60: # minute of the hour is 57
            self.time = self.time.replace(second=0, minute=0) + timedelta(hours=1)
            curr_minute = self.get_minute()
            curr_hour= self.get_hour()
            curr_time = self.get_time(curr_hour, curr_minute)

            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') 
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' 

            try:   
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
            logging.info(f'The filename for the quote being added during intialization: {filename}')     

        elif curr_minute + 3 == 61: # minute of the hour is 58
            self.time = self.time.replace(second=0, minute=1) + timedelta(hours=1)
            curr_minute = self.get_minute()
            curr_hour= self.get_hour()
            curr_time = self.get_time(curr_hour, curr_minute)

            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') 
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' 

            try:   
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
            logging.info(f'the filename for the quote being added during update: {filename}') 
                   
        elif curr_minute + 3 == 62: # minute of the hour is 59
            self.time = self.time.replace(second=0, minute=2) + timedelta(hours=1)
            curr_minute = self.get_minute()
            curr_hour= self.get_hour()
            curr_time = self.get_time(curr_hour, curr_minute)
            
            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') 
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' 
            
            try:   
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
            logging.info(f'the filename for the quote being added during update: {filename}')        

        else: # minute of the hour is not 57, 58, 59
            self.time = self.time.replace(second=0) + timedelta(minutes=3)
            curr_minute = self.get_minute()
            curr_time = self.get_time(curr_hour, curr_minute)

            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') 
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' 

            try:   
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
            logging.info(f'the filename for the quote being added during update: {filename}')        

        logging.info('update_buffer finish.\n')
        return self.quote_buffer

    def display_quote(self):
        '''
        This function reads the Image object at the front of
        the buffer and uses the epd.display() function to show
        it on the e-ink screen.
        '''
        try:
            logging.info('display_quote was called. Reading .bmp file from quote_buffer...')
            logging.info('the current time is: ' + str(self.time))
            quote_to_display = self.quote_buffer[0]                 # get the quote for the current time
            self.epd.init_fast()                                    # speeds up updates, according to waveshare support
            self.epd.display(self.epd.getbuffer(quote_to_display))  # display the quote
            logging.info('display_quote finish\n')
        except IOError as e:
            logging.info(f'error in display_quote: {e}\n')

    def main(self):
        '''
        This function displays the current time's quote, 
        removes it from the buffer, and updates the buffer.
        '''
        logging.info('main was called.')
        if self.get_hour() == 0 or self.get_hour() % 2 == 0 and self.get_minute() == 0:
            logging.info('Reintialize screen every other hour.')
            self.epd.init # Fully reinitialize the screen every two hours. This helps prevent image burn-in and increases the screen's lifespan.
        self.display_quote()                        # display the current quote
        self.quote_buffer.pop(0)                    # remove the current quote from buffer
        self.quote_buffer = self.update_buffer()    # call AFTER the current quote is displayed to reduce processing time.
        print('main finish. Quote was displayed and quote_buffer was updated.\n')

if __name__ == '__main__':
    try:
        logging.info("Book Quote Clock")
        clock = Clock()     # create clock object

        logging.info('Initializing and clearing the screen')
        clock.epd.init()    # initialize the screen
        clock.epd.Clear()   # clear screen

        logging.info('Displaying startup screen\n')
        startup_img = Image.open(os.path.join(clock.picdir, 'startup.bmp'))
        clock.epd.display(clock.epd.getbuffer(startup_img)) # display a startup screen
        time.sleep(30) # wait for the PI's system clock to update

        clock.quote_buffer = clock.init_buffer() # initialize the quote buffer with the first 3 quotes
        
        while True: 
            clock.main() # display the quote and update buffer
            clock.epd.sleep # put screen to sleep to increase its lifespan
            main_time = datetime.now() # get the current time
            time.sleep(60 - main_time.second) # sleep until the next minute

    except KeyboardInterrupt as e:
        logging.info('program interrupted:')
        logging.info(e)
        clock.epd.init() # wake the screen so that it can be cleared
        clock.epd.Clear()
        logging.info("clearing screen and shutting down...\n")
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        exit()
