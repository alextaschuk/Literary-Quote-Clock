'''module docstring'''
import csv
from datetime import datetime, timedelta
import logging
import random
import signal
import sys
import time

from PIL import Image, ImageFont

from waveshare_libraries import epd7in5_V2 # Waveshare's library for their 7.5 inch screen
from image_generator import generate_img, QUOTE_COLOR, QUOTES_PATH, FONT_PATH_REGULAR
from writer import Pen

logging.basicConfig(level=logging.DEBUG)

class Clock:
    '''
    A `Clock` obj contains all logic for creating and
    displaying the quotes to the screen.
    '''
    curr_image: Image.Image

    def __init__(self):
        self.quotes = []
        self.quote_buffer = []
        self.epd = epd7in5_V2.EPD()

        default_font = ImageFont.truetype(FONT_PATH_REGULAR, 1, ImageFont.Layout.BASIC)
        self.pen = Pen(default_font, QUOTE_COLOR)
        logging.info('created clock obj.')

    def get_image(self, quote_time: datetime) -> Image.Image:
        '''
        Find all possible quotes for the  provided `quote_time`, select one at random, and create an
        image for the quote to be displayed.

        - Returns an `Image` obj of the quote for the given time
        '''
        logging.info('get_image() called at %s.', str(datetime.now()))
        minute = quote_time.minute
        hour = quote_time.hour
        if minute < 10:
            minute = '0' + str(minute)
        if hour < 10:
            hour = '0' + str(hour)
        formatted_time = f'{hour}:{minute}' # e.g. '13:45'

        usable_rows = []
        include_metadata = True # include the quote's author and book title
        try:
            with open(QUOTES_PATH, newline='\n', encoding='UTF-8') as quotefile:
                quotefile.seek(0)
                quotereader = csv.DictReader(quotefile, delimiter='|')
                # go row-by-row through the CSV and get all quotes for the upcoming time
                for row in quotereader:
                    if row['time'] == formatted_time:
                        usable_rows.append(row)
        except FileNotFoundError:
            logging.error('File %s not found', QUOTES_PATH)

        # display an error message to the clock if quote is missing
        if not usable_rows:
            quote = f'Error: There is currently no quote for {formatted_time}.'
            usable_rows.append({'time': formatted_time, 'quote': quote, 'timestring': 'Error', 'author': '', 'title': ''})
            include_metadata = False
            logging.error('Missing quote for %s', formatted_time)

        row = usable_rows[random.randrange(0, len(usable_rows))] # the selected quote to display
        logging.info(f'selected quote for {formatted_time}: {row}')

        quote_image = generate_img(row, include_metadata, self.pen)
        logging.info('get_image() finished at %s.', str(datetime.now()))
        return quote_image


    def init_buffer(self):
        '''
        Initialize a buffer that stores the quotes to display for the next 3 minutes. 

        - E.g. this function is called at 09:40, so the buffer stores the quotes for 09:41, 09:42,
        and 09:43.
        '''
        logging.info('init_buffer() called at %s. Initializing quote_buffer…', str(datetime.now()))
        quote_time = datetime.now()

        while len(self.quote_buffer) < 3:
            # get the quotes that will be displayed one, two, and three minutes after current quote
            if quote_time.minute == 59: # if it's the 59th minute of the hour (e.g. 11:59)
                quote_time = quote_time.replace(minute=0,second=0, microsecond=0) + timedelta(hours=1) # set the time to the next hour (e.g. 12:00)
            else: # it is not the 59 minute (e.g. 13:21), so we only need the next minute
                quote_time = quote_time.replace(second=0) + timedelta(minutes=1) # set time to one minute from now (13:22)
            self.quote_buffer.append(self.get_image(quote_time=quote_time)) # add new quote
            self.pen.reset(self.pen.bbox.top_left_x, self.pen.bbox.top_left_y)
        logging.info('init_buffer() finished at %s.', str(datetime.now()))


    def update_buffer(self):
        # if a full refresh is performed, won't this fuck up the update buffer and skip a minute?
        # it boils down to whether or not a full refresh blocks the rest of the code from running
        '''
        Update `self.quote_buffer` by adding adding a quote for the time 3 minutes ahead of the
        currently displayed quote, then removing the currently displayed quote. If the current
        minute of the hour is 57, 58, or 59, the hour value also needs to get updated.
        '''
        logging.info("update_buffer() called at %s.", str(datetime.now()))

        quote_time = datetime.now()
        difference = 60 - quote_time.minute # number of mins until next hour

        if 0 < difference <= 3: # if the current minute is the 57th, 58th, or 59th of the hour
            logging.info('time being added to the quote is 57th, 58th, or 59th of the hour. current quote_time: %s', str(quote_time))
            quote_time = quote_time.replace(minute=(quote_time.minute + 3) % 10) + timedelta(hours=1) # e.g. at 13:58, get quote for 14:01
            logging.info('time being added to the quote is 57th, 58th, or 59th of the hour. updated quote_time: %s', str(quote_time))
        else:
            quote_time = quote_time.replace(minute = quote_time.minute + 3) # e.g. at 13:45, get quote for 13:48

        self.quote_buffer.append(self.get_image(quote_time=quote_time)) # generate image and add to buffer
        self.quote_buffer.pop(0) # remove the current quote from buffer
        self.pen.reset(self.pen.bbox.top_left_x, self.pen.bbox.top_left_y)
        logging.info('update_buffer() finished at %s. Image for %s:%s added.', str(datetime.now()), str(quote_time.hour), str(quote_time.minute))


    def display_quote(self):
        '''
        Read the `Image` obj at the front of the `self.quote_buffer` and
        use `epd.display()` to display it to the e-ink screen.
        '''
        try:
            logging.info('display_quote() called at %s.', str(datetime.now()))
            self.curr_image = self.quote_buffer[0]
            self.epd.display(self.epd.getbuffer(self.curr_image)) # display the current image
            self.epd.sleep() # put screen to sleep to increase its lifespan
            logging.info('display_quote finished at %s.', str(datetime.now()))
        except IOError as e:
            logging.info(f'IOError in display_quote: {e}')


    def main(self):
        '''
        Runs in a continuous loop once every minute to display
        the current time's quote, then update the `self.quote_buffer`.
        '''
        #logging.info(f'main() called at {str(datetime.now())}.')

        # Perform a full refresh every hour. This helps prevent "ghosting" and increases the
        # screen's lifespan.
        if datetime.now().minute == 59:
            logging.info('An hour has passed. Performing full refresh on screen.')
            self.epd.init()
            self.epd.Clear() # Then, clear the screen before displaying new quote
        else:
            self.epd.init_fast() # speeds up process of displaying image, according to Waveshare support

        if self.quote_buffer:
            self.display_quote() # display the current quote
            self.update_buffer()
        else: # only runs once
            logging.info('Displaying first quote and initializing buffer.')
            self.epd.display(self.epd.getbuffer(self.curr_image)) # display the first image when the clock turns on
            self.epd.sleep()
            self.init_buffer()

        logging.info('main() finished at %s.', str(datetime.now()))

def signal_handler(sig, frame):
    '''
    This function listens for `SIGINT` signals from the user. We use this because
    sending a `sudo shutdown -h now` command over SSH to the PI doesn't sent a
    `SIGINT` signal to the program, telling it to shutdown (i.e., clear the screen).
    I'm not totally sure why `sudo shutdown -h now` only triggers the program's
    shutdown process when sent directly from the PI and not over SSH, but this is my
    workaround to the issue.
    '''
    logging.info('sigint() called. Clearing screen and shutting clock down…\n')
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
        clock.pen.reset(clock.pen.bbox.top_left_x, clock.pen.bbox.top_left_y)
        try:
            while True:
                signal.signal(signal.SIGINT, signal_handler)
                clock.main()
                #logging.info(f'sleep for {(59 - datetime.now().second)} seconds before displaying next quote.')
                time.sleep(59 - datetime.now().second) # sleep until the next minute (called 1 sec early because of processing time to refresh screen)
        except BaseException as e:
            # if something breaks clear the screen in case its state is stuck
            logging.info(f'error: {e}')
            clock.epd.init()
            clock.epd.Clear()
            clock.epdconfig.module_exit(cleanup=True)
            exit()

    except KeyboardInterrupt as e:
        logging.info(f'program interrupted: {e}')
        logging.info("clearing screen and shutting clock down…\n")
        clock.epd.init() # wake the screen so that it can be cleared
        clock.epd.Clear()
        clock.epdconfig.module_exit(cleanup=True)
        exit()
