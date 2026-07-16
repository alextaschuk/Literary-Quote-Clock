'''A clock that tells the time using images of quotes.'''
import csv
from datetime import datetime, timedelta
import logging
import random
import signal
import sys
import time

from PIL import Image

from constants import ScreenOptions, SCREEN_TYPE, STARTUP_MSG, BUFFER_SIZE, INCLUDE_CREDITS
from image_generator import generate_img, QUOTES_PATH
from writer import Pen

if SCREEN_TYPE == ScreenOptions.IT8951:
    from IT8951 import constants
    from IT8951.display import AutoEPDDisplay
elif SCREEN_TYPE == ScreenOptions.WAVESHARE:
    from waveshare_libraries import epd7in5_V2 # Waveshare's library for their 7.5 inch screen


logging.basicConfig(level=logging.DEBUG)

class Clock:
    '''
    Determines which image should be displayed and when it should be displayed.

    This class contains all of logic to ensure that the correct quote is displayed on the screen and
    that the screen is updated with a new quote at the 0th second of each minute (or as close to it
    as possible).

    Attributes:
        quote_buffer (list[Image.Image]): A buffer that contains the images to be displayed for the
         next BUFFER_SIZE minutes, including the currently displayed image.
        epd (epd7in5_V2.EPD): Waveshare's EPD module to control the e-paper screen and what is
         displayed to it. 
        pen (Pen): The pen that is passed into the image generation function to convert a quote's
         row into an image.
    '''
    def __init__(self):
        self.quote_buffer: list[Image.Image] = []
        if SCREEN_TYPE == ScreenOptions.IT8951:
            self.display = AutoEPDDisplay(vcom=-2.79) # set to VCOM value that's on the FPC
        elif SCREEN_TYPE == ScreenOptions.WAVESHARE:
            self.epd = epd7in5_V2.EPD()

        self.pen = Pen()
        logging.info('created clock obj.')

    def get_image(self, quote_time: datetime) -> Image.Image:
        '''
        Find all possible quotes for the  provided `quote_time`, select one at random, and create an
        image for the quote to be displayed.

        Args:
            quote_time (datetime): The time of day to get a quote image for.
        Returns:
            quote_image (Image.Image): The image of the quote for the given time.
        Raises:
            FileNotFoundError: The path to the CSV of quotes is invalid.
        '''
        minute = '0' + str(quote_time.minute) if quote_time.minute < 10 else str(quote_time.minute)
        hour = '0' + str(quote_time.hour) if quote_time.hour < 10 else str(quote_time.hour)
        formatted_time = f'{hour}:{minute}'  # e.g. '13:45'
        usable_rows = []
        include_metadata = INCLUDE_CREDITS  # include the quote's author and book title

        # go row-by-row through the CSV and get all quotes for the upcoming time
        try:
            with open(QUOTES_PATH, newline='\n', encoding='UTF-8') as quotefile:
                quotefile.seek(0)
                quotereader = csv.DictReader(quotefile, delimiter='|')
                for row in quotereader:
                    if row['time'] == formatted_time:
                        usable_rows.append(row)
        except FileNotFoundError:
            logging.error('File %s not found', QUOTES_PATH)
            sys.exit(0)

        # display an error message to the clock if quote is missing
        if not usable_rows:
            quote = f'Error: There is currently no quote for {formatted_time}.'
            usable_rows.append({'time': formatted_time, 'quote': quote, 'timestring': 'Error', 'author': '', 'title': ''})
            include_metadata = False
            logging.error('Missing quote for %s', formatted_time)

        row = usable_rows[random.randrange(0, len(usable_rows))]
        logging.info('Selected a quote for %s: "%s..."', formatted_time, row['quote'][:50])

        quote_image = generate_img(row, include_metadata, self.pen)
        return quote_image

    def refresh_buffer(self):
        '''Update the clock's buffer with one or more new images of quotes.
        
        First, the image at the front of the buffer is removed (it is for the previous minute). Then,
        new quote(s) are added until the number of quotes in the buffer matches `BUFFER_SIZE`.
        '''
        del self.quote_buffer[0]
        curr_time = datetime.now()
        curr_time = curr_time.replace(
            minute=0) if curr_time.minute == 59 else curr_time.replace(minute=curr_time.minute + 1)

        for i in range(BUFFER_SIZE - len(self.quote_buffer)):
            quote_time = curr_time
            difference = 60 - quote_time.minute - len(self.quote_buffer)
            if difference <= 0:
                quote_time = quote_time.replace(minute=abs(difference)) + timedelta(hours=1)
            else:
                quote_time = quote_time.replace(minute=quote_time.minute + len(self.quote_buffer))
            self.quote_buffer.append(self.get_image(quote_time))


    def display_quote(self):
        '''
        Display the image at the front of the clock's buffer on the screen.

        Raises:
            IOError: An error occurred when displaying the image on the screen.
        '''
        try:
            self.quote_buffer[0].show()
            if SCREEN_TYPE == ScreenOptions.IT8951:
                self.display.frame_buf.paste(self.quote_buffer[0])
                self.display.draw_full(constants.DisplayModes.GC16)
                self.display.sleep() # necessary/real?
            elif SCREEN_TYPE == ScreenOptions.WAVESHARE:
                self.epd.display(self.epd.getbuffer(self.quote_buffer[0]))
                self.epd.sleep() # put screen to sleep to increase its lifespan
        except IOError as e:
            logging.error('Unable to display image: %s', str(e))
            self.wipe_screen()
            if SCREEN_TYPE == ScreenOptions.WAVESHARE:
                self.epdconfig.module_exit(cleanup=True)



    def wipe_screen(self):
        '''Wipe the screen when something breaks to prevent ghosting.'''
        logging.info("clearing the screen…\n")
        if SCREEN_TYPE == 'it8951':
            self.display.clear()
        else:
            self.epd.init()  # wake the screen so that it can be cleared
            self.epd.Clear()



    def main(self):
        '''Handles refreshing the screen, displaying quotes, and updating the clock's buffer.

        This function is continuously called once every minute and it performs four steps:

        1. If it is the 59th minute of the hour, perform a full refresh. This helps prevent ghosting
        and increases the screen's lifespan.
        2. Display the image at the front of the clock's buffer on the screen.
        3. Update the clock's buffer.
        4. Sleep until the next minute. This is called one second early because of processing time
        to update the screen with the next image.
        '''
        if datetime.now().minute == 59:
            logging.info('An hour has passed. Performing full refresh on screen.')
            if SCREEN_TYPE == ScreenOptions.IT8951:
                self.display.clear()
            elif SCREEN_TYPE == ScreenOptions.WAVESHARE:
                self.epd.init()
                self.epd.Clear()
        else:
            if SCREEN_TYPE == ScreenOptions.WAVESHARE:
                self.epd.init_fast() # speeds up displaying an image, according to Waveshare support
        self.display_quote()
        self.refresh_buffer()
        time.sleep(59 - datetime.now().second)


def signal_handler(sig, frame):
    '''
    Listen for `SIGINT` signals from the user.
    
    For some reason, sending a `sudo shutdown -h now` command over SSH to the Pi doesn't sent a
    `SIGINT` signal to the program, telling it to shutdown (i.e., clear the screen). I'm not totally
    sure why `sudo shutdown -h now` only triggers the program's shutdown process when sent directly
    from the Pi and not over SSH, but this is my workaround to the issue.
    - Code adapted from https://stackoverflow.com/a/1112350
    '''
    logging.info('sigint() called. Shutting clock down…\n')
    signal.signal(sig, signal.SIG_IGN)  # ignore additional signals
    clock.wipe_screen()
    if SCREEN_TYPE == ScreenOptions.WAVESHARE:
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
        startup_row = {'quote': STARTUP_MSG,'timestring': STARTUP_MSG, 'title': '', 'author': ''}
        startup_img = generate_img(startup_row, False, clock.pen)
        clock.epd.display(clock.epd.getbuffer(startup_img))
        clock.epd.sleep()

        time.sleep(30) # wait for the Pi's system clock to update after powering on (it has no RTC)
        first_img = clock.get_image(datetime.now())
        clock.quote_buffer.append(first_img)

        # This is bad practice, but it ensures that anything I might've missed is caught
        # so that the screen can be cleared before the program exits.
        try:
            while True:
                signal.signal(signal.SIGINT, signal_handler)
                clock.main()
        except Exception as e:
            logging.info('An error occured: %s', str(e))
            clock.wipe_screen()
            if SCREEN_TYPE == ScreenOptions.WAVESHARE:
                clock.epdconfig.module_exit(cleanup=True)
            sys.exit(0)

    except KeyboardInterrupt as e:
        logging.info('Program interrupted: %s', str(e))
        clock.wipe_screen()
        if SCREEN_TYPE == ScreenOptions.WAVESHARE:
            clock.epdconfig.module_exit(cleanup=True)
        sys.exit(0)
