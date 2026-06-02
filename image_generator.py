'''
This file will rows from a CSV file and do one of two things:
1. Read the CSV row-by-row, generate an image
'''
from PIL import Image, ImageDraw, ImageFont, ImageText
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(level=logging.DEBUG)

class ImageOutput(Enum):
    '''Determines whether images are saved to an /images folder, or
    an `Image` object is returned for each quote.
    '''
    SAVE = 1 # save images to an /images folder
    RETURN = 2 # return an Image object from TurnQuoteIntoImage()

class TextType(Enum):
    '''Describes which part of a quote is being passed into a function.'''
    QUOTE = 1
    CREDITS = 2 # string containing quote's book title and author

@dataclass
class BoundingBox:
    '''Stores the top left and bottom right
    coordinates of a bounding box to determine
    optimal font size.
    '''
    top_left_x:int
    top_left_y:int
    bottom_right_x:int
    bottom_right_y:int

@dataclass
class Fonts:
    '''Stores `FreeTypeFont` objects for
    all of the fonts that may be used
    '''
    regular:ImageFont.FreeTypeFont
    bold:ImageFont.FreeTypeFont
    italic:ImageFont.FreeTypeFont
    italic_bold:ImageFont.FreeTypeFont
    credit:ImageFont.FreeTypeFont

# screen config
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
QUOTE_WIDTH = int(SCREEN_WIDTH * 0.90) # 90% of screen size to ensure nothing is drawn out of bounds
QUOTE_HEIGHT = int(SCREEN_HEIGHT * 0.90)

# for a list of all image formats that Pillow supports, see
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#fully-supported-formats
IMAGE_FORMAT = 'bmp'

# image config
OUTPUT = ImageOutput.RETURN # should the main function save each image, or return them?
PATH = 'quotes.csv'
BG_COLOR = 255      # image's background color is white (#0xFFFFFF)
QUOTE_COLOR = 128   # non-timestring text is grey (#0x808080)
TIME_COLOR = 0      # timestring text is black (#0x000000)

# paths to font files
FONT_PATH_REGULAR = 'fonts/Bookerly.ttf' # the font the quote will be written in *fntname_norm
FONT_PATH_ITALIC = 'fonts/Bookerly-Italic.ttf'  # used for italicized words
FONT_PATH_BOLD = 'fonts/Bookerly-Bold.ttf'                 # timestring words
FONT_PATH_ITALIC_BOLD = 'fonts/Bookerly-Bold-Italic.ttf'   # italicized timestring words
FONT_PATH_CREDIT = FONT_PATH_BOLD # the font the book's title and Author's name will be written in

def wrap_text(text:str, bbox:BoundingBox, fonts:Fonts, timestr: Optional[str] = '') -> str | None:
    '''TODO'''
    words = text.split()
    lines: list[str] = [""]
    x = bbox.top_left_x
    y = bbox.top_left_y
    timestr_begin, timestr_end = -1, -1

    if timestr:
        try:
            timestr_begin = text.lower().index(timestr.lower())
            timestr_end = timestr_begin + len(timestr) - 1
            #time_words = timestr.split()
        except ValueError as exc:
            print('Error at: ' + text)
            raise LookupError from exc

    for i, word in enumerate(words):
        font = fonts.bold if timestr_begin <= i <= timestr_end else fonts.regular

        if i + 1 < len(words):
            word += ' '
            first_char_next_word = words[i + 1][0]
        else:
            first_char_next_word = ''

        # get the next word's first char to adjust for kerning.
        # see https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
        word_len = int(font.getlength(word + first_char_next_word) - font.getlength(first_char_next_word))

        # a single word cannot be longer than one line
        if word_len > bbox.bottom_right_x - bbox.top_left_x:
            return None

        if x == bbox.top_left_x:
            # this is the first word of a line
            lines[-1] = word
            x += int(font.getlength(word))
        else:
            if x + word_len > bbox.bottom_right_x:
                # get the current line's height before moving to the next line
                curr_line = ImageText.Text(lines[-1], font)
                line_bbox = curr_line.get_bbox()
                line_height = int(line_bbox[3] - line_bbox[1])
                #print(f'font size:{font.size} line height in wrap_text:{line_height}')
                #y += line_height
                y += font.getbbox("A")[3] + 4

                # add the current word to a new line and reset length
                lines.append(word)
                x = bbox.top_left_x
            else:
                lines[-1] = f'{lines[-1]} {word}'
            x += word_len

        # current wrapping writes text past bbox
        if y > bbox.bottom_right_y:
            return None

    return '\n'.join(lines)


def find_optimal_font_size(text:str, bbox: BoundingBox, text_type:TextType,
                           timestr: Optional[str] = ''):
    '''Find maximum possible font size of a given bounding box without having to actually draw the
    text.

    Args:
        text (str): The text to fit inside the bounding box.
        bbox (BoundingBox): A bounding box to fill with the text.
        timestr (str): **Optional**: If passing in a quote, include the quote's timestring.

    Returns:
        int | None: The optimal font size once found, or `None` if a word is too
        long and cannot fit on one line.
    '''
    min_size = 12
    max_size = 150 if text_type == TextType.QUOTE else 100
    optimal_size = None
    best_fit_lines: list[str] = [""]

    # binary search to find optimal font size
    while min_size <= max_size:
        mid_size = min_size + (max_size - min_size) // 2
        lines: list[str] = [""]

        fonts = Fonts(
            regular=ImageFont.truetype(FONT_PATH_REGULAR, mid_size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FONT_PATH_BOLD, mid_size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FONT_PATH_ITALIC, mid_size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, mid_size,
                                           ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FONT_PATH_CREDIT, mid_size, ImageFont.Layout.BASIC)
        )

        timestr_begin, timestr_end = -1, -1
        if timestr:
            try:
                timestr_begin = text.lower().index(timestr.lower())
                timestr_end = timestr_begin + len(timestr) - 1
                #time_words = timestr.split()
            except ValueError as exc:
                print('Error at: ' + text)
                raise LookupError from exc

        lines = wrap_text(text, bbox, fonts)
        if lines:
            optimal_size = mid_size
            min_size = mid_size + 1
            best_fit_lines = lines
        else: # text didn't fit
            max_size = mid_size - 1
    return (optimal_size, best_fit_lines)


def write_in_bbox(text:str, bbox:BoundingBox, text_type:TextType, img:Image.Image, timestr: Optional[str] = ""):
    '''Write a given string into a bounding box.

    Args:
        text (str): The text to write inside of the bounding box.
        bbox (BoundingBox): The bounding box that the string will fill.
        img (Image.Image): The Image to write the text on.
        timestr (Optional[str]): A substring that contains the quote's time.
    '''
    canvas = ImageDraw.Draw(img)
    canvas.rectangle((bbox.top_left_x, bbox.top_left_y, bbox.bottom_right_x, bbox.bottom_right_y))
    fnt_size, wrapped_lines = find_optimal_font_size(text, bbox, text_type)
    print(f'optimal fontsize: {fnt_size}')

    if fnt_size:
        fonts = Fonts(
            regular=ImageFont.truetype(FONT_PATH_REGULAR, fnt_size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FONT_PATH_BOLD, fnt_size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FONT_PATH_ITALIC, fnt_size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, fnt_size,
                                           ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FONT_PATH_CREDIT, fnt_size, ImageFont.Layout.BASIC)
        )
        write = canvas.text
        quote_words = text.split()
        canvas = ImageDraw.Draw(img)
        font = fonts.regular
        color = QUOTE_COLOR if text_type == TextType.QUOTE else TIME_COLOR

        y = bbox.top_left_y
        for line in wrapped_lines.splitlines():
            x = bbox.top_left_x
            for i, word in enumerate(line.split()):
                # get the next word's first char to adjust for kerning.
                # see https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
                if i + 1 < len(line):
                    word += ' '
                    next_words_first_char = quote_words[i + 1][0]
                else:
                    next_words_first_char = ""
                word_len = int(font.getlength(word + next_words_first_char) - font.getlength(next_words_first_char))

                write((x,y), word, color, font, anchor='lm') # anchored = top left of bbox
                x += word_len
            y += font.getbbox("A")[3] + 4


def get_quote_img(index:int, time:str, quote:str, timestring:str, author:str, title:str, include_metadata: bool):
    '''Generate an image of a single quote.

    Args:
        index (int): Row number of the quote.
        time (str): Hour and minute the quote is for (e.g., "13:43")
        quote (str): The entire quote.
        timestring (str): Substring of the quote that tells the time.
        author (str): Author of the book.
        title (str): Title of the book.
        include_metadata (bool): True to print quote's author and title, False to discard.
    
    Returns:
        Image: An image with the quote drawn on it.
    '''
    # mode='L' constrains the image to 8-bit grayscale
    quote_image = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)

    quote_bbox = BoundingBox(
        top_left_x=0,
        top_left_y=0,
        bottom_right_x=QUOTE_WIDTH,
        bottom_right_y=QUOTE_HEIGHT
    )

    if include_metadata:
        mdata_bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.55),
            top_left_y = int(SCREEN_HEIGHT * 0.80),
            bottom_right_x = int(SCREEN_WIDTH),
            bottom_right_y = int(SCREEN_HEIGHT)
            )

        metadata = f'—{title.strip()}, {author.strip()}' # e.g. '—Dune, Frank Herbert
        write_in_bbox(metadata, mdata_bbox, TextType.CREDITS, quote_image)

        quote_bbox.bottom_right_y = int(QUOTE_HEIGHT)

    write_in_bbox(quote, quote_bbox, TextType.QUOTE, quote_image)

    quote_image.show()


if __name__ == "__main__":
    #pass
    time = '12:00'
    quote = 'The man crawled across a dune top. He was a mote caught in the glare of the noon sun.'
    timestr = 'noon'
    #author = 'Frank Herbert'
    #title = 'Dune'
    author = 'Hunter S. Thompson'
    title = "Fear and Loathing: On the Campaign Trail '72"
    get_quote_img(0, time, quote, timestr, author, title, True)
