''' This file contains all logic for displaying images to the screen. '''

# imports for time stuff
from datetime import datetime, timedelta # for getting the times
import os
import glob
import random
import signal

# libraries for displaying image on screen
import sys
import logging
import time
from PIL import Image
from waveshare_libraries import epd7in5_V2 # Waveshare's library for their 7.5 inch screen

logging.basicConfig(level=logging.DEBUG)

class Clock:
    ''' All logic for creating and updating the quote buffer, and displaying the quotes '''
    curr_time: str
    quotes: list
    filename: str
    quote_buffer: list

    def __init__(self):
        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'Literary-Quote-Clock/images') # path to .bmp files
        logging.info(self.picdir)
        self.time = datetime.now()
        self.quote_buffer = []
        self.quotes = []
        self.epd = epd7in5_V2.EPD()

        logging.info('clock obj was made.')

    def get_minute(self) -> int:
        '''
        Returns the current minute as an integer.
        - For example, 30 is returned for 13:30
        '''
        return self.time.minute

    def get_hour(self) -> int:
        '''
        Returns the current hour as an integer.
        - For example, 13 is returned for 13:30
        - For example, 01 is returned for 01:30
        '''
        return self.time.hour

    def get_time(self, minute: int, hour: int) -> str: # e.g. if it's 1:30 PM, this returns '1330'
        '''
        Returns the current time as a string in the 24-hour format.
        - For example, '1330' is returned for 13:30.
        '''
        if minute < 10:
            minute = '0' + str(minute)
        if hour < 10: # if it is midnight, get_hour() returns 0, so we need to append another 0 to have '00'
            hour = '0' + str(hour)
        return str(hour) + str(minute)

    def get_quotes(self, filename) -> list:
        '''
        A helper function for buffer_quotes that returns all possible quotes for a given minute.
        - Returns a list of all filepaths for a given minute.
        '''
        filename = 'images/' + filename
        if glob.glob(filename):                 # get all quotes for the current time
            self.quotes = glob.glob(filename)   # stores all quotes for the current time; we will choose a random quote from the list
        return self.quotes

    def init_buffer(self) -> list:
        '''
        Initializes the buffer with the first 3 quotes; one for the current time
        (e.g. 09:40), one for the time in one minute (e.g., 09:41), and one for
        the time in two minutes (e.g. 09:42).
        - Returns a list of three (open) Image objects
        '''
        logging.info(f'init_buffer() called. self.time: {str(self.time)}. Initializing quote_buffer...')
        self.time = datetime.now() # update the time
        curr_time = self.get_time(minute=self.get_minute(), hour=self.get_hour())

        while len(self.quote_buffer) < 3:
            # this is a short-term soultion until I find quotes for times that don't have one yet.
            try:
                self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') # used to find all quotes for a specific time e.g. 'quote_1510_*.bmp'
                filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' # pick 1 quote at random from the get_quotes() call
                image_quote = Image.open(os.path.join(self.picdir, filename))
                self.quote_buffer.append(image_quote)
            except FileNotFoundError:
                logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
                if len(self.quote_buffer) > 0:
                    self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap
                else:
                    time.sleep(60) # in the event that the first quote doesn't exist, wait a minute
            logging.info(f'The filename for the quote being added during intialization: {filename}')     

            # get the quotes that will be displayed one and two minutes after current quote
            if self.get_minute() == 59: # if it's the 59th minute of the hour (e.g. 11:59)
                self.time = self.time.replace(minute=0,second=0, microsecond=0) + timedelta(hours=1) # set the time to the next hour (e.g. 12:00)
            else: # it is not the 59 minute, so we only need the next minute
                self.time = self.time.replace(second=0) + timedelta(minutes=1) # set the time to one minute from now
            
            curr_time = self.get_time(minute=self.get_minute(), hour=self.get_hour())

        self.time = datetime.now() # set time back to actual current time
        logging.info(f'init_buffer() finish. Buffer initialized.')
        return self.quote_buffer

    def update_buffer(self) -> list:
        '''
        To update the buffer, we need to add the quote that's 2 minutes ahead of the currently displayed quote.  
        Because the next quote to be added is 3 minutes ahead of the current quote that is being removed, we 
        add 3 minutes rather than 2 to get the new quote. Due to this logic, we need to check if the current 
        minute is 57, 58, or 59 because the hour also needs to get updated when this is the case. 

        Returns an updated list of three Image objects
        '''

        logging.info(f"update_buffer() called. self.time: {str(self.time)}. Updating quote_buffer...")
        self.time = datetime.now() # update the time
        
        difference = 60 - self.get_minute() # number of mins until next hour
        if 0 < difference <= 3: # if the current minute is the 57th, 58th, or 59th of the hour
            self.time = self.time.replace(minute=(self.get_minute() + 3) % 10) + timedelta(hours=1) # e.g. at 13:58 we get quote for 14:01
        else:
            self.time = self.time.replace(minute = self.get_minute() + 3) # e.g. at 13:45 we get quote for 13:48
        
        curr_time = self.get_time(minute=self.get_minute(), hour=self.get_hour())
        try:
            self.quotes = self.get_quotes('quote_' + curr_time + '_*' + '.bmp') # get all possible quotes for the minute
            filename = 'quote_' + curr_time + '_' + str(random.randrange(0, len(self.quotes))) + '.bmp' # pick one quote at random

            image_quote = Image.open(os.path.join(self.picdir, filename))
            self.quote_buffer.append(image_quote) # add the quote to the buffer
            self.quote_buffer[0].close() # close the Image obj of the current quote
            self.quote_buffer.pop(0)     # remove the current quote from buffer

            logging.info(f'Filename for the quote being added to the buffer: {filename}') 
        except FileNotFoundError:
            logging.info(f'Error! File {filename} for the time {curr_time} does not exist.\n')
            self.quote_buffer.append(self.quote_buffer[0]) # add the current time back into the buffer to fill the gap

        self.time = datetime.now() # set time back to actual current time
        logging.info('update_buffer() finish. Buffer updated.')

    def display_quote(self):
        '''
        This function reads the Image object at the front of
        the buffer and uses epd.display() to show it on the
        e-ink screen.
        '''
        try:
            logging.info('display_quote() called. Reading .bmp file from quote_buffer...')
            logging.info('the current time is: ' + str(self.time))
            quote_to_display = self.quote_buffer[0] # get the quote for the current time
            self.epd.display(self.epd.getbuffer(quote_to_display))  # display the quote
            self.epd.sleep() # put screen to sleep to increase its lifespan
            logging.info('display_quote finish\n')
        except IOError as e:
            logging.info(f'error in display_quote: {e}\n')

    def main(self):
        '''
        This function displays the current time's quote, 
        removes it from the buffer, and updates the buffer.
        '''
        logging.info('main() called.')
        if (self.get_minute() % 10) == 0:
            logging.info('10 minutes have passed. Performing full refresh on screen.')
            self.epd.init() # Do a full refresh every 10 minutes. This helps prevent "ghosting" and increases the screen's lifespan.
            self.epd.Clear() # Then, clear the screen before displaying new quote
        else:
            self.epd.init_fast() # speeds up updates, according to waveshare support
        self.display_quote()     # display the current quote
        self.update_buffer()     # call AFTER the current quote is displayed to reduce processing time.
        logging.info('main() finish.\n')

def signal_handler(sig, frame):
    '''
    This function listens for `SIGINT` signals from the user.
    We use this because sending a `sudo shutdown -h now`
    command over SSH to the PI doesn't sent a `SIGINT` signal
    to the program, telling it to shutdown (i.e., clear the
    screen). I'm not totally sure why `sudo shutdown -h now`
    doesn't trigger the program's shutdown process when sent
    over SSH, but does when sent directly from the PI, but
    this is a workaround to the issue.
    '''
    logging.info('sigint() called.')
    signal.signal(sig, signal.SIG_IGN) # ignore additional signals
    clock.epd.init() # wake the screen so that it can be cleared
    clock.epd.Clear()
    logging.info("clearing screen and shutting clock down...\n")
    clock.epdconfig.module_exit(cleanup=True)
    sys.exit(0)

if __name__ == '__main__':
    try:
        logging.info("Literary Quote Clock Started")
        clock = Clock()     # create Clock object

        logging.info('Initializing and clearing the screen')
        clock.epd.init()    # initialize the screen
        clock.epd.Clear()   # clear screen

        logging.info('Displaying startup screen\n')
        try:
            #with Image.open(os.path.join(clock.picdir, 'startup.bmp')) as startup_img: # use this if startup.bmp is in /images
            with Image.open('startup.bmp') as startup_img: # use this if startup.bmp is in root dir
                clock.epd.display(clock.epd.getbuffer(startup_img)) # display a startup screen
        except FileNotFoundError:
            logging.error('error startup.bmp image not found')

        clock.epd.sleep() # put the screen to sleep
        time.sleep(30) # wait for the PI's system clock to update
        clock.quote_buffer = clock.init_buffer() # initialize the quote buffer with the first 3 quotes

        while True:
            signal.signal(signal.SIGINT, signal_handler)
            clock.main() # display the quote and update buffer
            curr_time = datetime.now() # get the current time
            time.sleep(59 - curr_time.second) # sleep until the next minute (this is called 1 sec early because of processing time to show the next image)
            logging.info(f'sleeping for {59 - curr_time.second} seconds before displaying next quote.')

    except KeyboardInterrupt as e:
        logging.info('program interrupted:')
        logging.info(e)
        clock.epd.init() # wake the screen so that it can be cleared
        clock.epd.Clear()
        logging.info("clearing screen and shutting clock down...\n")
        clock.epdconfig.module_exit(cleanup=True)
        exit()
