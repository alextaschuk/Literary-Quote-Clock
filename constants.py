'''
Global constants that are to be modified according to the type of screen used or personal preference

Consolidates all of the things that could change depending on the type of screen that you're using
or according to personal preference. While this may not be the best solution, it eliminates the need
to go searching through multiple files to change things.
'''
from enum import Enum

#################
# Screen Config #
#################
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
STARTUP_MSG = 'Literary Quote Clock is Starting…'

class ScreenOptions(Enum):
    '''docstring'''
    IT8951    = 1
    WAVESHARE = 2

SCREEN_TYPE = ScreenOptions.WAVESHARE

#############################
# Image Config and Settings #
    # color is in RGB
#############################
BG_COLOR     = 255 # image's background color is white
QUOTE_COLOR  = 128 # non-timestring text is grey
TIME_COLOR   = 0   # timestring text is black
CREDIT_COLOR = 0   # credit text is black

#QUOTES_PATH = 'quotes.csv'
QUOTES_PATH = 'misc/test.csv'
IMAGE_PATH = 'images/'

# for a list of all image formats that Pillow supports, see
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#fully-supported-formats
IMAGE_FORMAT = 'bmp'
INCLUDE_CREDITS = True # print the quote's author and the book that it comes from?

###############
# Text Config #
###############
MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 150 # depending on image dimensions, this may need to be increased

################
# Clock Config #
################
BUFFER_SIZE = 3 # number of quotes to buffer
