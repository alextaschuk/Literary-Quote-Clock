''' This file contains all logic for displaying images to the screen. '''

# imports for time stuff
from datetime import datetime, timedelta # for getting the times
import os
import random
import signal

# libraries for displaying image on screen
import sys
import logging
import time
import csv
from PIL import Image
from waveshare_libraries import epd7in5_V2 # Waveshare's library for their 7.5 inch screen
from get_image import TurnQuoteIntoImage

logging.basicConfig(level=logging.DEBUG)

class Clock:
    '''
    A clock obj contains all logic for 
    creating and displaying the quotes
    to the screen.
    '''

    CSV_PATH = 'quotes.csv'
    time: datetime
    quotes: list
    curr_image: Image
    quote_buffer: list


    def __init__(self):
        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'Literary-Quote-Clock/images') # path to .bmp files
        self.time = datetime.now()
        self.quotes = []
        self.quote_buffer = []
        self.epd = epd7in5_V2.EPD()

        logging.info('clock obj was made.')

    def get_image(self, quote_time: datetime) -> Image:
        '''
        This function finds all possible quotes for the 
        provided `quote_time`, selects one at random, and
        generates an image for the quote to be displayed.
        - Returns an `Image` obj
        '''
        logging.info(f'get_image() called at {str(self.time)}.')
        min = quote_time.minute
        hour = quote_time.hour
        if min < 10:
            min = '0' + str(min)
        if hour < 10: # if it is midnight, time.hour returns 0, so we need to append another 0 to have '00'
            hour = '0' + str(hour)

        formatted_time = f'{hour}:{min}' # e.g. '13:45'
        quotes = []
        try:
            with open(self.CSV_PATH, newline='\n', encoding='UTF-8') as quotefile:
                quotefile.seek(0)
                quotereader = csv.DictReader(quotefile, delimiter='|')

                # go row-by-row through the CSV and get all quotes for the upcoming time
                for i, row in enumerate(quotereader):
                    if row['time'] == formatted_time:
                        quotes.append(row)

            logging.info(f'list of quotes: {str(quotes)}')
            row = quotes[random.randrange(0, len(quotes))] # the selected quote to display
            return TurnQuoteIntoImage(i, row['time'], row['quote'], row['timestring'], row['author'], row['title'])
        except FileNotFoundError:
            logging.error(f'Error: file {self.CSV_PATH} not found')

    def init_buffer(self) -> list:
        '''
        Initializes the buffer that will store the quotes
        to display for the next 3 minutes. E.g. `init_buffer()`
        is called at 09:40, so the buffer stores the quotes for
        09:41, 09:42, and 09:43.
        - Returns a list of three (open) Image objects
        '''

        logging.info(f'init_buffer() called at {str(self.time)}. Initializing quote_buffer...')
        quote_time = datetime.now() # update the time

        for i in range(3):
            # get the quotes that will be displayed one, two, and three minutes after current quote
            if quote_time.minute == 59: # if it's the 59th minute of the hour (e.g. 11:59)
                quote_time = quote_time.replace(minute=0,second=0, microsecond=0) + timedelta(hours=1) # set the time to the next hour (e.g. 12:00)
            else: # it is not the 59 minute (e.g. 13:21), so we only need the next minute
                quote_time = quote_time.replace(second=0) + timedelta(minutes=1) # set the time to one minute from now (13:22)
            
            self.quote_buffer[i] = self.get_image(quote_time=quote_time)

        self.time = datetime.now() # set time back to actual current time
        logging.info(f'init_buffer() finished at {str(self.time)}.')
        return self.quote_buffer


    def update_buffer(self) -> list:
        '''
        To update the buffer, we need to add the quote that's 2 minutes ahead of the currently displayed quote.  
        Because the next quote to be added is 3 minutes ahead of the current quote that is being removed, we 
        add 3 minutes rather than 2 to get the new quote. Due to this logic, we need to check if the current 
        minute is 57, 58, or 59 because the hour also needs to get updated when this is the case. 

        - Returns an updated list of three Image objects
        '''

        logging.info(f"update_buffer() called at {str(self.time)}.")
        quote_time = datetime.now() # update the time
        
        difference = 60 - quote_time.minute # number of mins until next hour
        if 0 < difference <= 3: # if the current minute is the 57th, 58th, or 59th of the hour
            quote_time = quote_time.replace(minute=(quote_time.minute + 3) % 10) + timedelta(hours=1) # e.g. at 13:58 we get quote for 14:01
        else:
            quote_time = quote_time.replace(minute = quote_time.minute + 3) # e.g. at 13:45 we get quote for 13:48
        
            image_quote = self.get_image(self.time)
            self.quote_buffer.append(image_quote) # add the quote to the buffer
            self.quote_buffer.pop(0)     # remove the current quote from buffer

        logging.info(f'update_buffer() finished at {str(self.time)}. Image for {str(quote_time.hour)}:{str(quote_time.minute)} added.')

    def display_quote(self):
        '''
        Reads the `Image` object at the front of
        the buffer and uses `epd.display()` to show it on the
        e-ink screen.
        '''
        self.time = datetime.now() # update the time
        try:
            logging.info(f'display_quote() called at {str(self.time)}.')
            self.curr_image = self.quote_buffer[0]
            self.epd.display(self.epd.getbuffer(self.curr_image)) # display the current image
            self.epd.sleep() # put screen to sleep to increase its lifespan
            logging.info(f'display_quote finished at {str(self.time)}.')
        except IOError as e:
            logging.info(f'error in display_quote: {e}')


    def main(self):
        '''
        This function displays the current time's quote, 
        removes it from the buffer, and updates the buffer.
        '''
        logging.info(f'main() called at {str(self.time)}.')

        if self.time.minute == 0:
            logging.info('60 minutes have passed. Performing full refresh on screen.')
            self.epd.init() # Perform full refresh every hour. This helps prevent "ghosting" and increases the screen's lifespan.
            self.epd.Clear() # Then clear the screen before displaying new quote
        else:
            self.epd.init_fast() # speeds up process of displaying new image, according to Waveshare support
        
        if self.quote_buffer:
            self.display_quote() # display the current quote
            self.update_buffer()
        else:
            self.init_buffer()
            
        logging.info(f'main() finished at {str(self.time)}.')

def signal_handler(sig, frame):
    '''
    This function listens for `SIGINT` signals from the user.
    We use this because sending a `sudo shutdown -h now`
    command over SSH to the PI doesn't sent a `SIGINT` signal
    to the program, telling it to shutdown (i.e., clear the
    screen). I'm not totally sure why `sudo shutdown -h now`
    only triggers the program's shutdown process when sent
    directly from the PI and not over SSH, but this is my
    workaround to the issue.
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
        clock = Clock()

        logging.info('Initializing and clearing the screen')
        clock.epd.init()
        clock.epd.Clear()

        logging.info('Displaying startup screen')
        try:
            with Image.open('startup.bmp') as startup_img: # use this if startup.bmp is in root dir
               clock.epd.display(clock.epd.getbuffer(startup_img)) # display a startup screen
            clock.epd.sleep() # put the screen to sleep
        except FileNotFoundError:
            logging.error('Error! startup.bmp image not found')

        time.sleep(30) # wait for the PI's system clock to update (it has no RTC)
        clock.get_image(quote_time=datetime.now()) # get the first image
        try:
            while True:
                signal.signal(signal.SIGINT, signal_handler)
                clock.main() # displays the quote and performs full refresh if necessary
                logging.info(f'sleep for {(59 - datetime.now().second)} seconds before displaying next quote.')
                time.sleep(59 - datetime.now().second) # sleep until the next minute (this is called 1 sec early because of processing time to show the next image)
        except BaseException as e:
            logging.info(f'error: {e}')
            clock.epd.init()
            clock.epd.Clear()
            clock.epdconfig.module_exit(cleanup=True)
            exit()

    except KeyboardInterrupt as e:
        logging.info('program interrupted:')
        logging.info(e)
        clock.epd.init() # wake the screen so that it can be cleared
        clock.epd.Clear()
        logging.info("clearing screen and shutting clock down...\n")
        clock.epdconfig.module_exit(cleanup=True)
        exit()
