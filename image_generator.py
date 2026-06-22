'''
This file will rows from a CSV file and do one of two things:
1. Read the CSV row-by-row, generate an image
'''
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import unicodedata
from PIL import Image, ImageDraw, ImageFont
from check_format import check_italic, check_bold, check_new_line, check_blank_line
from pen import Pen, Formatters, FormatDelimiter

logging.basicConfig(level=logging.DEBUG)

class ImageOutput(Enum):
    '''Determine what `get_quote_img()` should do with each generated image: save it to an /images
    folder, or return an `Image` object.
    '''
    SAVE    = 1 # save images to an /images folder
    RETURN  = 2 # return an Image object from TurnQuoteIntoImage()

class TextType(Enum):
    '''Describes which part of a quote is being passed into a function.'''
    QUOTE   = 1
    CREDITS = 2 # author and book title of the quote

@dataclass
class BoundingBox:
    '''Defines the top left and bottom right (x,y) coordinates of a bounding box to determine
    optimal font size.
    '''
    top_left_x      :int
    top_left_y      :int
    bottom_right_x  :int
    bottom_right_y  :int

@dataclass
class Fonts:
    '''Consolidates `FreeTypeFont` objects for all of the fonts that may be used.'''
    regular     :ImageFont.FreeTypeFont
    bold        :ImageFont.FreeTypeFont
    italic      :ImageFont.FreeTypeFont
    italic_bold :ImageFont.FreeTypeFont
    credit      :ImageFont.FreeTypeFont

# screen config
SCREEN_WIDTH    = 800
SCREEN_HEIGHT   = 480

# image config
OUTPUT      = ImageOutput.RETURN # should the main function save an image, or return it?
QUOTE_PATH  = 'quotes.csv'
BG_COLOR    = 255   # image's background color is white (#0xFFFFFF)
QUOTE_COLOR = 128   # non-timestring text is grey (#0x808080)
TIME_COLOR  = 0     # timestring text is black (#0x000000)

# for a list of all image formats that Pillow supports, see
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#fully-supported-formats
IMAGE_FORMAT = 'bmp'

# paths to font files
FONT_PATH_REGULAR       = 'fonts/Bookerly.ttf'              # non-timestring words
FONT_PATH_BOLD          = 'fonts/Bookerly-Bold.ttf'         # timestring words
FONT_PATH_ITALIC        = 'fonts/Bookerly-Italic.ttf'       # italicized words
FONT_PATH_ITALIC_BOLD   = 'fonts/Bookerly-Bold-Italic.ttf'  # italicized timestring words
FONT_PATH_CREDIT        = FONT_PATH_BOLD                    # for the quote's book title and author

MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 100

# formatting characters
ITALIC  =   '◻'
BOLD    =   '◯'
TIMESTR =   '|'

def write_format(word:str, formatter:str):
    '''
    TODO: change formatting logic so that italic, bold, and timestr text is wrapped by 
    2 characters for an entire substr (◻an◻ ◻example◻ --> ◻an example◻).

    Also need to fix/finish logic for text wrapping to use bold font for timestr

    maybe make a `Pen` object that stores necessary info like current font, fontsize, 
    ImageDraw, current x and y coords, etc. Then use that pen when calculating fontsize and 
    drawing on the object. It also could store variables to track how many of a certain
    formatting character it has seen. When, for example, when it is trying to calculate
    fontsize if a font is too big, before returning 0 and a blank str, it "resets" the 
    pen back to the top left of the bbox, the counters back to 0, etc. So we'd also need
    a reset_pen() function.
    '''
    if word.count(formatter) == 2:
        pass


def get_word_len(words:list[str], curr_word:str, curr_word_pos:int, num_words:int,
                 font:ImageFont.FreeTypeFont):
    '''Calculates the length of a word. 

    For a more accurate calculation, the Pillow docs suggest getting the next word's first
    character to adjuct for kerning.
        - See https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
    
    Args:
        words (list[str]): All of the words in the string to be drawn to an image.
        curr_word (str): The word whose length is being calculated.
        curr_word_pos (int): The index of `curr_word` in `words`.
        num_words (int): The number of words in `words` (i.e., its length).
        font (ImageFont.FreeTypeFont): The font that is being used to draw `curr_word`.
    '''
    if curr_word_pos + 1 < num_words:
        curr_word += ' '
        first_char_next_word = words[curr_word_pos + 1][0]
    else: # current word is the last word of the text
        first_char_next_word = ''

    #TODO: replace this kind of stuff to return default values (float) as late as possible for max accuracy. then convert to int
    return int(font.getlength(curr_word + first_char_next_word) - font.getlength(first_char_next_word))


def check_font(word:str, fonts:Fonts, is_timestr:Optional[bool]=False):
    '''Determine which font should be used to write a word.'''
    font = fonts.regular
    italic = False
    if check_italic(word):
        font = fonts.italic
        word = unicodedata.normalize('NFKD', word.replace(ITALIC, ''))
        italic = True # just so that we don't have to check twice
    if check_bold(word) or is_timestr:
        font = fonts.italic_bold if italic else fonts.bold
        word = unicodedata.normalize('NFKD', word.replace(BOLD, ''))
    return (font, word)

def wrap_text(text:str, bbox:BoundingBox, fonts:Fonts, timestr: Optional[str] = '') -> str:
    '''Helper to `find_optimal_font_size()`. Wraps text so that it doesn't overflow past the
    rightmost x coordinate of the bbox.
    '''
    lines: list[str] = [""]
    x = bbox.top_left_x
    y = bbox.top_left_y

    #timestr_begin, timestr_end = -1, -1
    #if timestr:
    #    try:
    #        timestr_begin = text.lower().index(timestr.lower())
    #        timestr_end = timestr_begin + len(timestr) - 1
    #        time_words = timestr.split()
    #    except ValueError as exc:
    #        print('Error at: ' + text)
    #        raise LookupError from exc

    # iterate over the text word-by-word and try to place each word on the current line. If the word
    # cannot fit, move down one line and place it there instead.
    words = text.split()
    for i, word in enumerate(words):
        temp_word = word
        #if timestr_begin <= i <= timestr_end:
        #    font, temp_word = check_font(temp_word, fonts, True)
        #else:
        #    font, temp_word = check_font(temp_word, fonts, False)
        font, temp_word = check_font(temp_word, fonts)
        word_len = get_word_len(words, word, i, len(words), font)

        # a single word cannot be longer than one line
        if word_len > bbox.bottom_right_x - bbox.top_left_x:
            return ''

        if x + word_len > bbox.bottom_right_x:
            # move to the next line, add the current word to the line, and reset x coord
            y += font.getbbox("A")[3] + 4 #TODO: Replace with get_lineheight()
            lines.append(temp_word)
            x = bbox.top_left_x
        else:
            lines[-1] = f'{lines[-1]} {temp_word}' # add the current word to the current line
        x += word_len


        #if x == bbox.top_left_x: # current word is the first word of a line
        #    lines[-1] = word
        #    x += int(font.getlength(word))
        #else:
        #    if x + word_len > bbox.bottom_right_x:
        #        # move to the next line, add the current word to the line, and reset x coord
        #        y += font.getbbox("A")[3] + 4
        #        lines.append(word)
        #        x = bbox.top_left_x
        #    else:
        #        lines[-1] = f'{lines[-1]} {word}' # add the current word to the current line
        #    x += word_len

        # current wrapping writes text past bbox (need to reduce font size)
        if y > bbox.bottom_right_y:
            #print(f'y={y} check greater than bottom right y for text="{text}". bot right y={bbox.bottom_right_y}. fontsize={font.size}')
            return ''
        else:
            print(f'y={y} check. bot right y={bbox.bottom_right_y}. fontsize={font.size}')

    wrapped = '\n'.join(lines)

    # verify that the wrapping fits
    # TODO figure out how pillow calculates bbox and manually implement height calculation so that i dont have to make all of these objects each time
    temp_img = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)
    canvas = ImageDraw.Draw(temp_img)
    pil_bbox = canvas.multiline_textbbox((bbox.top_left_x, bbox.top_left_y), wrapped, fonts.regular)

    if pil_bbox[3] > bbox.bottom_right_y:
        #print(f'pillow bbox={pil_bbox[3]} check greater than bottom right y for text="{text}". y={y}. bot right y={bbox.bottom_right_y}. fontsize={font.size}')
        return ''
    return wrapped


def find_optimal_font_size(text:str, bbox: BoundingBox, text_type:TextType,
                           timestr: Optional[str] = ''):
    '''Find the maximum possible font size that the text can be written in for a given bounding box.

    Args:
        text (str): The text to fit inside the bounding box.
        bbox (BoundingBox): A bounding box to fill with the text.
        timestr (str): **Optional**: If `text` is a quote, include its timestring.

    Returns:
        Tuple (int, str): If a valid font size is found, the tuple contains the optimal font size
        and a string containing the text broken up with newline delimiters to fit in the bbox
        horizontally. If the text cannot fit in the bbox with a font size >= `MIN_FONT_SIZE`, the
        tuple contains `(0, '')`.
    '''
    min_size = MIN_FONT_SIZE
    max_size = MAX_FONT_SIZE
    optimal_size = 0
    best_fit_lines = ""

    # binary search to find optimal font size
    while min_size <= max_size:
        mid_size = min_size + (max_size - min_size) // 2
        lines = ""

        fonts = Fonts(
            regular=ImageFont.truetype(FONT_PATH_REGULAR, mid_size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FONT_PATH_BOLD, mid_size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FONT_PATH_ITALIC, mid_size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, mid_size,
                                           ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FONT_PATH_CREDIT, mid_size, ImageFont.Layout.BASIC)
        )

        lines = wrap_text(text, bbox, fonts, timestr)
        if lines:
            optimal_size = mid_size
            min_size = mid_size + 1
            best_fit_lines = lines
        else: # text didn't fit
            max_size = mid_size - 1

    lines_height = 0
    for line in best_fit_lines.splitlines():
        lines_height += int(fonts.regular.getbbox("A")[3] + 4) # TODO: Replace with get_lineheight()

    if text_type == TextType.QUOTE:
        bbox.bottom_right_y = bbox.top_left_y + lines_height
    else:
        bbox.top_left_y = bbox.bottom_right_y - lines_height
    return (optimal_size, best_fit_lines)


def write_in_bbox(text:str, bbox:BoundingBox, text_type:TextType, img:Image.Image,
                  timestr: Optional[str] = ""):
    '''Write a given string into a bounding box.

    Args:
        text (str): The text to write inside of the bounding box.
        bbox (BoundingBox): The bounding box that the string will fill.
        img (Image.Image): The Image to write the text on.
        timestr (Optional[str]): A substring that contains the quote's time.
    '''
    canvas = ImageDraw.Draw(img)
    write = canvas.text
    canvas = ImageDraw.Draw(img)
    quote_words = text.split()
    color = QUOTE_COLOR if text_type == TextType.QUOTE else TIME_COLOR
    y = bbox.top_left_y

    timestr_begin, timestr_end = -1, -1
    if timestr:
        try:
            timestr_begin = text.lower().index(timestr.lower())
            timestr_end = timestr_begin + len(timestr)
            time_words = timestr.split()
            # wrap the timestr with '|' so that we can find it again when drawing each word.
            temp_words = text[:timestr_begin]
            temp_words += f'{TIMESTR}{text[timestr_begin:timestr_end]}{TIMESTR}'
            temp_words += text[timestr_end:]
            text = temp_words
        except ValueError as exc:
            print('Error at: ' + text)
            raise LookupError from exc

    fnt_size, wrapped_lines = find_optimal_font_size(text, bbox, text_type, timestr)
    print(f'optimal fontsize: {fnt_size}')

    if fnt_size <= MIN_FONT_SIZE:
        raise ValueError(f'Error: Text "{text}" is too long and doesn’t fit in bbox {bbox}.')

    fonts = Fonts(
        regular=ImageFont.truetype(FONT_PATH_REGULAR, fnt_size, ImageFont.Layout.BASIC),
        bold=ImageFont.truetype(FONT_PATH_BOLD, fnt_size, ImageFont.Layout.BASIC),
        italic=ImageFont.truetype(FONT_PATH_ITALIC, fnt_size, ImageFont.Layout.BASIC),
        italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, fnt_size,
                                       ImageFont.Layout.BASIC),
        credit=ImageFont.truetype(FONT_PATH_CREDIT, fnt_size, ImageFont.Layout.BASIC)
    )
    curr_font = fonts.regular

    for line in wrapped_lines.splitlines():
        x = bbox.top_left_x
        words = line.split()
        for i, word in enumerate(words):
            if timestr_begin <= i <= timestr_end:
                curr_font, word = check_font(word, fonts, True)
            else:
                curr_font, word = check_font(word, fonts, False)

            word_len = get_word_len(words, word, i, len(words), curr_font)
            write((x,y), word, color, curr_font)
            x += word_len
        y += curr_font.getbbox("A")[3] + 4 # TODO: Replace with get_lineheight()


def get_quote_img(index:int, time:str, quote:str, timestring:str, author:str, title:str,
                  include_credits: bool, pen:Pen):
    '''Generate an image of a single quote.

    The quote's credits are first drawn onto the image (optional), constrained by the
    `mdata_bbox`. The quote is then drawn onto the image constrained by a bbox that ends
    just above the credits bbox. If credits are not included, then the quote's bbox
    takes up the entire height of the screen.

    Args:
        index (int): Row number of the quote.
        time (str): Hour and minute the quote is for (e.g., "13:43").
        quote (str): The entire quote. (e.g., "It is noon.")
        timestring (str): Substring of the quote that tells the time. (e.g., "noon")
        author (str): Author of the book.
        title (str): Title of the book.
        include_credits (bool): True to print quote's author and title, False to discard.
    
    Returns:
        Image: An image with the quote and credits drawn on it.
    '''
    # mode='L' constrains the image to 8-bit grayscale
    quote_image = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)

    quote_bbox = BoundingBox(
        top_left_x=0,
        top_left_y=0,
        bottom_right_x=int(SCREEN_WIDTH),
        bottom_right_y=int(SCREEN_HEIGHT)
    )

    if include_credits:
        cred_bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.45),
            top_left_y = int(SCREEN_HEIGHT * 0.85),
            bottom_right_x = int(SCREEN_WIDTH),
            bottom_right_y = int(SCREEN_HEIGHT * 0.99)
            )

        # Write the credits onto the image, then resize the quote's bbox to just above the
        # top of the credit's bbox
        quote_credit = f'—{title.strip()}, {author.strip()}' # e.g. '—Dune, Frank Herbert
        write_in_bbox(quote_credit, cred_bbox, TextType.CREDITS, quote_image)
        quote_bbox.bottom_right_y = int(cred_bbox.top_left_y * 0.99)

    write_in_bbox(quote, quote_bbox, TextType.QUOTE, quote_image, timestring)
    quote_image.show()


if __name__ == "__main__":
    #TIME = '12:00'
    #QUOTE = 'The man crawled across a dune top. He was a mote caught in the glare of the noon sun.'
    #TIMESTRING = 'noon'
    #AUTHOR = 'Frank Herbert'
    #TITLE = 'Dune'
    TIME = '06:21'
    QUOTE = "The whipped mules dragged the wagon on through a flooded branch that submerged thirty yards of the road and stood up around the bushes and tree-trunks on either side so that they had no rootage, and I watched where and how deep the wheels went while I idled the motor and lighter Gudger's and my own cigarette. It was twenty-one past six."
    TIMESTRING = "twenty-one past six."
    AUTHOR = "James Agee and Walker Evans"
    TITLE = 'Let Us Now Praise Famous Men'
    #TIME='00:00'
    #QUOTE='The house is empty, but Eugene sings as if he had for audience all the crowned heads of Europe. The garden door is open and the odor of wet leaves sops in and the rain blends with Eugene’s ◻angoisse◻ and ◻tristesse◻. At midnight, after the spectators have saturated the hall with perspiration and foul breaths, I return to sleep on a bench. The exit light, swimming in a halo of tobacco smoke, sheds a faint light on the lower corner of the asbestos curtain; I close my eyes every night on an artificial eye…'
    #TIMESTRING='midnight'
    #TITLE='Tropic of Cancer'
    #AUTHOR='Henry Miller'
    default_font = ImageFont.truetype(FONT_PATH_REGULAR, 0, ImageFont.Layout.BASIC)
    pen = Pen(font=default_font, x=0, y=0)
    get_quote_img(0, TIME, QUOTE, TIMESTRING, AUTHOR, TITLE, include_credits=True, pen=pen)
