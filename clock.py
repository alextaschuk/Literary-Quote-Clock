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
    A clock obj contains all logic for creating and
    displaying the quotes to the screen.
    '''

    CSV_PATH = 'quotes.csv'
    curr_image: Image

    def __init__(self):
        self.quotes = []
        self.quote_buffer = []
        self.epd = epd7in5_V2.EPD()
        logging.info('created clock obj.')

    def get_image(self, quote_time: datetime) -> Image:
        '''
        This function finds all possible quotes for the 
        provided `quote_time`, selects one at random, and
        generates an image for the quote to be displayed.
        - Returns an `Image` obj
        '''
        logging.info(f'get_image() called at {str(datetime.now())}.')
        minute = quote_time.minute
        hour = quote_time.hour
        if minute < 10:
            minute = '0' + str(minute)
        if hour < 10: # if it is midnight, time.hour returns 0, so we need to append another 0 to have '00'
            hour = '0' + str(hour)

        formatted_time = f'{hour}:{minute}' # e.g. '13:45'
        quotes = [] # not to be confused w/ self.quotes
        include_metadata = True # true = include the author and book's title of the quote
        try:
            with open(self.CSV_PATH, newline='\n', encoding='UTF-8') as quotefile:
                quotefile.seek(0)
                quotereader = csv.DictReader(quotefile, delimiter='|')

                # go row-by-row through the CSV and get all quotes for the upcoming time
                for i, row in enumerate(quotereader):
                    if row['time'] == formatted_time:
                        quotes.append(row)

            # if there's at least one quote for a time, check that the timestring is in the
            # quote, and display error image if mismatch
            if quotes:
                row = quotes[random.randrange(0, len(quotes))] # the selected quote to display
                logging.info(f'selected quote for {formatted_time}: {row}')

                valid_quote = row['quote'].replace('\n',' ')
                try:
                    temp = valid_quote.lower().index(row['timestring'].lower())
                except ValueError:
                    quote = f'Error: Quote that begins with {quote[:10]} does not have a matching timestring.'
                    row = {'time': formatted_time, 'quote': quote, 'timestring': 'Error', 'author': '', 'title': ''}
                    include_metadata = False
                    logging.error(f'Error: The timestring was not found in the quote.\n The quote throwing the error is: {valid_quote} \nIts substr is: {row["timestring"]}')

            # if quote is missing altogether, display error message
            else:
                quote= f'Error: There is currently no quote for {formatted_time}.'
                row = {'time': formatted_time, 'quote': quote, 'timestring': 'Error', 'author': '', 'title': ''}
                include_metadata = False
                logging.info(f'Missing quote for {formatted_time}')
        except FileNotFoundError:
            logging.error(f'Error: file {self.CSV_PATH} not found')
        
        logging.info(f'get_image() finished at {str(datetime.now())}.')
        return TurnQuoteIntoImage(i, row['time'], row['quote'], row['timestring'], row['author'], row['title'], include_metadata)


    def init_buffer(self) -> list:
        '''
        Initializes the buffer that will store the quotes
        to display for the next 3 minutes. E.g. `init_buffer()`
        is called at 09:40, so the buffer stores the quotes for
        09:41, 09:42, and 09:43.
        - Returns a list of three Image objects
        '''
        logging.info(f'init_buffer() called at {str(datetime.now())}. Initializing quote_buffer...')
        quote_time = datetime.now()
        
        while len(self.quote_buffer) < 3:
            # get the quotes that will be displayed one, two, and three minutes after current quote
            if quote_time.minute == 59: # if it's the 59th minute of the hour (e.g. 11:59)
                quote_time = quote_time.replace(minute=0,second=0, microsecond=0) + timedelta(hours=1) # set the time to the next hour (e.g. 12:00)
            else: # it is not the 59 minute (e.g. 13:21), so we only need the next minute
                quote_time = quote_time.replace(second=0) + timedelta(minutes=1) # set time to one minute from now (13:22)
            self.quote_buffer.append(self.get_image(quote_time=quote_time)) # add new quote

        logging.info(f'init_buffer() finished at {str(datetime.now())}.')


    def update_buffer(self) -> list:
        '''
        To update the buffer, we need to add the quote that's 2 minutes ahead of the currently
        displayed quote. Because the next quote to be added is 3 minutes ahead of the current quote
        that is being removed, we add 3 minutes rather than 2 to get the new quote. Due to this
        logic, we need to check if the current  minute is 57, 58, or 59 because the hour also needs
        to get updated when this is the case. 

        - Returns an updated list of three Image objects
        '''
        logging.info(f"update_buffer() called at {str(datetime.now())}.")

        quote_time = datetime.now() # update the time
        difference = 60 - quote_time.minute # number of mins until next hour

        if 0 < difference <= 3: # if the current minute is the 57th, 58th, or 59th of the hour
            logging.info(f'time being added to the quote is 57th, 58th, or 59th of the hour. current quote_time: {str(quote_time)}')
            quote_time = quote_time.replace(minute=(quote_time.minute + 3) % 10) + timedelta(hours=1) # e.g. at 13:58 we get quote for 14:01
            logging.info(f'time being added to the quote is 57th, 58th, or 59th of the hour. updated quote_time: {str(quote_time)}')
        else:
            quote_time = quote_time.replace(minute = quote_time.minute + 3) # e.g. at 13:45 we get quote for 13:48

        self.quote_buffer.append(self.get_image(quote_time=quote_time)) # get quote and add to buffer
        self.quote_buffer.pop(0) # remove the current quote from buffer

        logging.info(f'update_buffer() finished at {str(datetime.now())}. Image for {str(quote_time.hour)}:{str(quote_time.minute)} added.')


    def display_quote(self):
        '''
        Reads the `Image` object at the front of
        the buffer and uses `epd.display()` to show it on the
        e-ink screen.
        '''
        try:
            logging.info(f'display_quote() called at {str(datetime.now())}.')
            self.curr_image = self.quote_buffer[0]
            self.epd.display(self.epd.getbuffer(self.curr_image)) # display the current image
            self.epd.sleep() # put screen to sleep to increase its lifespan
            logging.info(f'display_quote finished at {str(datetime.now())}.')
        except IOError as e:
            logging.info('IOError in display_quote:', e)


    def main(self):
        '''
        This function displays the current time's quote, 
        removes it from the buffer, and updates the buffer.
        '''
        logging.info(f'main() called at {str(datetime.now())}.')

        if datetime.now().minute == 29 or  datetime.now().minute == 59:
            logging.info('30 minutes have passed. Performing full refresh on screen.')
            self.epd.init() # Perform full refresh every half hour. This helps prevent "ghosting" and increases the screen's lifespan.
            self.epd.Clear() # Then clear the screen before displaying new quote
        else:
            self.epd.init_fast() # speeds up process of displaying image, according to Waveshare support

        if self.quote_buffer:
            self.display_quote() # display the current quote
            self.update_buffer()
        else: # only runs once
            logging.info(f'Displaying first quote and initializing buffer.')
            self.epd.display(self.epd.getbuffer(self.curr_image)) # display the first image when the clock turns on
            self.epd.sleep()
            self.init_buffer() # initialize the buffer
            
        logging.info(f'main() finished at {str(datetime.now())}.')

def signal_handler(sig, frame):
    '''
    This function listens for `SIGINT` signals from the user. We use this because
    sending a `sudo shutdown -h now` command over SSH to the PI doesn't sent a
    `SIGINT` signal to the program, telling it to shutdown (i.e., clear the screen).
    I'm not totally sure why `sudo shutdown -h now` only triggers the program's
    shutdown process when sent directly from the PI and not over SSH, but this is my
    workaround to the issue.
    '''
    logging.info('sigint() called. Clearing screen and shutting clock down...\n')
    signal.signal(sig, signal.SIG_IGN) # ignore additional signals
    clock.epd.init() # wake the screen so that it can be cleared
    clock.epd.Clear()
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
            with Image.open('startup.bmp') as startup_img:
                clock.epd.display(clock.epd.getbuffer(startup_img)) # display a startup screen
            clock.epd.sleep() # put the screen to sleep
        except FileNotFoundError:
            logging.error('Error! startup.bmp image not found')

        time.sleep(30) # wait for the PI's system clock to update (it has no RTC)
        clock.curr_image = clock.get_image(quote_time=datetime.now()) # get the first image
        try:
            while True:
                signal.signal(signal.SIGINT, signal_handler)
                clock.main()
                logging.info(f'sleep for {(59 - datetime.now().second)} seconds before displaying next quote.')
                time.sleep(59 - datetime.now().second) # sleep until the next minute (called 1 sec early because of processing time to refresh screen)
        except BaseException as e:
            # if something breaks clear the screen in case its state is stuck
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
