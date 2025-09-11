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
    curr_time: str
    quotes: list
    filename: str
    curr_image: Image

    def __init__(self):
        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'Literary-Quote-Clock/images') # path to .bmp files
        logging.info(self.picdir)
        self.time = datetime.now()
        self.quotes = []
        self.epd = epd7in5_V2.EPD()

        logging.info('clock obj was made.')

    def get_image(self, quote_time: datetime):
        '''
        This function generates an image for the quote to be displayed.
        - Note: we pass a `datetime` obj instead of just `self.time` because
        the inital quote that is displayed whenever the clock is first
        started will be wrong otherwise.
        '''
        logging.info(f'get_image() called at {str(quote_time)}.')

        if quote_time.minute == 59: # if the current minute is the 59th of the hour
            quote_time = quote_time.replace(minute=0) + timedelta(hours=1) # e.g. at 13:59 we get quote for 14:00
        else:
            quote_time = quote_time.replace(minute = self.time.minute + 1) # e.g. at 13:45 we get quote for 13:48
        
        min = quote_time.minute
        hour = quote_time.hour
        if min < 10:
            min = '0' + str(min)
        if hour < 10: # if it is midnight, time.hour returns 0, so we need to append another 0 to have '00'
            hour = '0' + str(hour)

        formatted_time = f'{hour}:{min}' # e.g. '13:45'
        quotes = []
        try:
            # we're going to go row-by-row through the csv and get all quotes for the upcoming time
            with open(self.CSV_PATH, newline='\n', encoding='UTF-8') as quotefile:
                quotefile.seek(0)
                quotereader = csv.DictReader(quotefile, delimiter='|')
                for i, row in enumerate(quotereader):
                    if row['time'] == formatted_time:
                        quotes.append(row)
            logging.info(f'list of quotes: {str(quotes)}')
            row = quotes[random.randrange(0, len(quotes))]
            self.curr_image = TurnQuoteIntoImage(i, row['time'], row['quote'], row['timestring'], row['author'], row['title'])
        except FileNotFoundError:
            logging.error(f'Error: file {self.CSV_PATH} not found')


    def display_quote(self):
        '''
        Reads the `Image` object at the front of
        the buffer and uses `epd.display()` to show it on the
        e-ink screen.
        '''
        self.time = datetime.now() # update the time
        try:
            logging.info(f'display_quote() called at {str(self.time)}.')
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
        
        self.display_quote() # display the current quote
        self.get_image(quote_time=self.time)# get the next image to display
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
        clock.get_image(quote_time=clock.time) # get the first image

        while True:
            signal.signal(signal.SIGINT, signal_handler)
            clock.main() # displays the quote and performs full refresh if necessary
            logging.info(f'sleep for {(59 - datetime.now().second)} seconds before displaying next quote.')
            time.sleep(59 - datetime.now().second) # sleep until the next minute (this is called 1 sec early because of processing time to show the next image)

    except KeyboardInterrupt as e:
        logging.info('program interrupted:')
        logging.info(e)
        clock.epd.init() # wake the screen so that it can be cleared
        clock.epd.Clear()
        logging.info("clearing screen and shutting clock down...\n")
        clock.epdconfig.module_exit(cleanup=True)
        exit()
