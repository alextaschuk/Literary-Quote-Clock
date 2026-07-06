'''
Generate an image of a quote and either save it as a file or return it as an `Image.Image` object.

To save all of the quote images to an /images folder, run this file. To return an `Image.Image`
object for a single quote, import the `generate_img()` function into your file and call it as
needed.

TODO:
        - add logic for parsing CSV
        - add logic for saving each image / returning one image
        - add functionality for newline and double newline
    - see if it's worth it/possible to make global Fonts object
    - add logic to choose screen orientation (horizontal vs vertical)
    - update README
        - fix logic so that the color of credit text is correct
    - add logic to split credits into two lines
    - write tests
        - fix formatting in quotes.csv and my-quotes.csv
    - (for future) match delimiters to markdown (will need to handle instances where, e.g., * is
    actually used)
    - add check if quote has any formatting at all. if not, write entire quote word-by-word instead.
        - change timestr check to return error message if it's missing
    - find better delim chars for newline and double newline
'''
import csv
from enum import Enum
import logging
import os
from os import path
from sys import argv
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from writer import BoundingBox, CharacterDelimiters, WordDelimiters, Fonts, Pen, TextType

logging.basicConfig(level=logging.DEBUG)

class ImageOutput(Enum):
    '''Determine what `generate_img()` should do with each generated image: save it to an /images
    folder, or return an `Image` object.
    '''
    SAVE   = 1  # save images to an /images folder
    RETURN = 2  # return an Image object from TurnQuoteIntoImage()


'''Screen Config'''
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 480


'''Image Config'''
# color is in RGB
BG_COLOR     = 255 # image's background color is white
QUOTE_COLOR  = 128 # non-timestring text is grey
TIME_COLOR   = 0   # timestring text is black
CREDIT_COLOR = 0   # credit text is black

OUTPUT      = ImageOutput.SAVE  # should the main function save an image, or return it?
QUOTES_PATH  = 'quotes.csv'
IMAGE_PATH = 'images/'

# for a list of all image formats that Pillow supports, see
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#fully-supported-formats
IMAGE_FORMAT = 'bmp'

'''Text Config'''
FONT_PATH_REGULAR     = 'fonts/Bookerly.ttf'                # non-timestring words
FONT_PATH_BOLD        = 'fonts/Bookerly-Bold.ttf'           # timestring words
FONT_PATH_ITALIC      = 'fonts/Bookerly-Italic.ttf'         # italicized words
FONT_PATH_ITALIC_BOLD = 'fonts/Bookerly-Bold-Italic.ttf'    # italicized timestring words
FONT_PATH_CREDIT      = FONT_PATH_BOLD # for the quote's book title and author

MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 150

def format_char(char:str, fonts:Fonts, pen:Pen) -> str:
    '''Determine the font and color to write a character with.

    If the character is a delimiter, an empty string is returned.

    Args:
        char (str): The character to be written.
        fonts (Fonts): Contains the possible fonts that may be used to write the character.
        pen (Pen): The pen used to write the character to the image.
    
    Returns:
      char (str): An empty string if the passed in character is a delimiting character. Otherwise,
      the `char` that is passed in by the caller is returned back.
    '''
    italic_count = 0 # determines if the font should be bold or italic-bold
    found_delimiter = False

    # check each delimiter and update their counters as needed, along with the pen's font and color
    for delim in pen.char_delimiters:
        if char in (dir(WordDelimiters())):
            return '' # TODO: replace to check all attributes in WordDelimiters
        if char == delim.character:
            delim.count += 1
            char = ''
        if delim.count == 1:
            found_delimiter = True # not necessarily true, but prevents font from being reset to regular prematurely
            if delim.character == CharacterDelimiters.ITALIC:
                italic_count = delim.count
                pen.font = fonts.italic
                pen.color = QUOTE_COLOR
            elif delim.character in (CharacterDelimiters.BOLD, CharacterDelimiters.TIMESTR):
                pen.font = fonts.italic_bold if italic_count > 0 else fonts.bold
                pen.color = TIME_COLOR
        elif delim.count >= 2:
            delim.count = 0
            found_delimiter = True

    if not found_delimiter:
        pen.font = fonts.regular
        pen.color = QUOTE_COLOR if pen.text_type == TextType.QUOTE else TIME_COLOR

    return char

def format_word(word:str, lines:list[str], word_len:int, pen:Pen):
    '''Check if a word needs to be moved onto a new line, separately from text wrapping.
    
    Args:
        word (str): The word to be formatted.
        lines (list[str]): Each element represents a line of text.
        word_len (int): The length (in pixels) of the text
         - NOT `len(word)`
        pen (Pen): The pen used to write the word.
    '''
    add_line = False
    if WordDelimiters.NEWLINE in word:
        pen.coords['x'] = pen.bbox.top_left_x
        pen.coords['y'] += int(pen.font.getbbox("A")[3] + 4)
        add_line = True
    elif WordDelimiters.DOUBLE_NEWLINE in word:
        pen.coords['x'] = pen.bbox.top_left_x
        pen.coords['y'] += 2 * int(pen.font.getbbox("A")[3] + 4)
        add_line = True
        lines.append(' ')
        # need to fix.

    if pen.coords['x'] + word_len > pen.bbox.bottom_right_x or add_line:
        # move to the next line, add the current word to the line, and reset x coord
        # TODO: Replace with get_lineheight()
        pen.coords['y'] += int(pen.font.getbbox("A")[3] + 4)
        lines.append(word)
        pen.coords['x'] = pen.bbox.top_left_x
    else:
        # add the current word to the current line
        lines[-1] = f'{lines[-1]} {word}'


def draw_word(img: Image.Image, word: str, fonts: Fonts, pen: Pen):
    '''Draw a word onto an image character-by-character.
    
    Args:
        img (Image.Image): The image object the word is drawn onto.
        word (str): The word to be drawn.
        fonts (Fonts): Contains the possible fonts that may be used to write the word.
        pen (Pen): The pen used to write the word.
    '''
    canvas = ImageDraw.Draw(img)
    write = canvas.text
    for char in word:
        char = format_char(char, fonts, pen)
        if char == '':
            continue
        write((pen.coords['x'], pen.coords['y']), char, pen.color, pen.font)
        pen.coords['x'] += int(pen.font.getlength(char))

    # add a space after each word
    write((pen.coords['x'], pen.coords['y']), ' ', pen.color, pen.font)
    pen.coords['x'] += int(pen.font.getlength(' '))

    for delimiter in pen.char_delimiters:
        if delimiter.count >= 2:
            delimiter.count = 0
            pen.font = fonts.regular


def wrap_text(text: str, fonts: Fonts, pen: Pen) -> str:
    '''Helper to `find_optimal_font_size()`. Wraps text so that it doesn't overflow past the
    rightmost x coordinate of the bbox.

    Args:
        text (str): The text to be wrapped.
        fonts (Fonts): Contains the possible fonts that may be used to write the word.
        pen (Pen): The pen used to write the text.

    Returns:
        wrapped (str):
    '''
    lines: list[str] = [""]
    pen.coords['x'] = pen.bbox.top_left_x
    pen.coords['y'] = pen.bbox.top_left_y
    # iterate over the text character-by-character and try to place each word on the current line.
    # If the word cannot fit, move down one line and place it there instead. Then, move the pen
    # right to write the next word.
    words = text.split()
    for word in words:
        word_len = 0
        for char in word:
            char = format_char(char, fonts, pen)
            if char == '':
                continue
            word_len += int(pen.font.getlength(char))

        # a single word cannot be longer than one line
        if word_len > pen.bbox.bottom_right_x - pen.bbox.top_left_x:
            pen.reset(pen.bbox.top_left_x, pen.bbox.top_left_y)
            return ''

        word_len += int(pen.font.getlength(' ')) # simulate space after word
        format_word(word, lines, word_len, pen)
        pen.coords['x'] += word_len

        # current wrapping writes text past bbox (need to reduce font size)
        if pen.coords['y'] > pen.bbox.bottom_right_y:
            pen.reset(pen.bbox.top_left_x, pen.bbox.top_left_y)
            return ''

    wrapped = '\n'.join(lines)

    # verify that the wrapping fits
    # TODO figure out how pillow calculates bbox and manually implement height calculation so that i dont have to make all of these objects each time
    temp_img = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)
    canvas = ImageDraw.Draw(temp_img)
    pil_bbox = canvas.multiline_textbbox((pen.bbox.top_left_x, pen.bbox.top_left_y), wrapped, fonts.regular)

    if pil_bbox[3] > pen.bbox.bottom_right_y:
        pen.reset(pen.bbox.top_left_x, pen.bbox.top_left_y)
        return ''
    return wrapped


def find_optimal_font_size(text: str, bbox: BoundingBox, text_type: TextType):
    '''Find the maximum possible font size that the text can be written in for a given bounding box.

    Args:
        text (str): The text to fit inside the bounding box.
        bbox (BoundingBox): A bounding box to fill with the text.
        text_type (TextType): Tells the function if the text is a quote or credits.

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

    inital_font = ImageFont.truetype(FONT_PATH_REGULAR, min_size, ImageFont.Layout.BASIC)
    temp_pen = Pen(inital_font, QUOTE_COLOR)
    temp_pen.bbox = bbox
    temp_pen.text = text

    # use binary search to find optimal font size
    while min_size <= max_size:
        mid_size = min_size + (max_size - min_size) // 2
        lines = ""

        fonts = Fonts(
            regular=ImageFont.truetype(FONT_PATH_REGULAR, mid_size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FONT_PATH_BOLD, mid_size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FONT_PATH_ITALIC, mid_size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, mid_size, ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FONT_PATH_CREDIT, mid_size, ImageFont.Layout.BASIC)
        )
        temp_pen.font = fonts.regular
        lines = wrap_text(text, fonts, temp_pen)
        if lines:
            optimal_size = mid_size
            min_size = mid_size + 1
            best_fit_lines = lines
        else:  # text didn't fit
            max_size = mid_size - 1

    lines_height = 0
    for line in best_fit_lines.splitlines():
        # TODO: Replace with get_lineheight()
        lines_height += int(fonts.regular.getbbox("A")[3] + 4)

    if text_type == TextType.QUOTE:
        bbox.bottom_right_y = bbox.top_left_y + lines_height  # left-justified
    else:
        bbox.top_left_y = bbox.bottom_right_y - lines_height  # right-justified for credits
    return (optimal_size, best_fit_lines)

def find_timestr_indices(pen:Pen, timestr: str):
    '''Find the index that the timestring begins and ends in the quote.'''
    timestr_begin = pen.text.lower().index(timestr.lower())
    timestr_end = timestr_begin + len(timestr)
    return (timestr_begin, timestr_end)


def write_in_bbox(img: Image.Image, pen: Pen, timestr: Optional[str] = ""):
    '''Write a given string into a bounding box.

    Args:
        img (Image.Image): The Image to write the text on.
        pen (Pen): The pen used to write the quote.
        timestr (Optional[str]): A substring that contains the quote's time.
    '''
    # wrap the timestr with '|' so that we can find it again when drawing each word.
    # write an error message instead if the timestring isn't found.
    timestr_begin, timestr_end = -1, -1
    if pen.text_type == TextType.QUOTE and timestr:
        try:
            timestr_begin, timestr_end = find_timestr_indices(pen, timestr)
        except ValueError:
            pen.text = f'Error: Timestring doesn\'t match or isn\'t found in quote starting with \
                         "{pen.text[:30]}..."'
            timestr = 'Error:'
            timestr_begin, timestr_end = find_timestr_indices(pen, timestr)
            logging.error('Timestring doesn\'t match or isn\'t found in quote starting with' \
                         '"%s..."', pen.text[:30])
        delim = CharacterDelimiters.TIMESTR
        quote = pen.text[:timestr_begin]
        quote += f'{delim}{pen.text[timestr_begin:timestr_end]}{delim}'
        quote += pen.text[timestr_end:]
        pen.text = quote

    pen.font.size, wrapped_lines = find_optimal_font_size(pen.text, pen.bbox, pen.text_type)

    if pen.font.size <= MIN_FONT_SIZE:
        bbox_repr = repr(pen.bbox)
        logging.error('Text starting with "%s..." is too long and doesn\'t fit in bbox=%s with minimum font=%i',pen.text[:30], bbox_repr, MIN_FONT_SIZE)

    fonts = Fonts(
        regular=ImageFont.truetype(FONT_PATH_REGULAR, pen.font.size, ImageFont.Layout.BASIC),
        bold=ImageFont.truetype(FONT_PATH_BOLD, pen.font.size, ImageFont.Layout.BASIC),
        italic=ImageFont.truetype(FONT_PATH_ITALIC, pen.font.size, ImageFont.Layout.BASIC),
        italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, pen.font.size, ImageFont.Layout.BASIC),
        credit=ImageFont.truetype(FONT_PATH_CREDIT, pen.font.size, ImageFont.Layout.BASIC)
    )

    pen.coords['y'] = pen.bbox.top_left_y
    for line in wrapped_lines.splitlines():
        pen.coords['x'] = pen.bbox.top_left_x
        words = line.split()
        for word in words:
            draw_word(img, word, fonts, pen)
        # TODO: Replace with get_lineheight()
        pen.coords['y'] += int(pen.font.getbbox("A")[3] + 4)


def generate_img(row:dict, include_credits:bool, pen:Pen):
    '''Generate an image of a single quote.

    The quote's credits are first drawn onto the image (optional), constrained by the
    `mdata_bbox`. The quote is then drawn onto the image constrained by a bbox that ends
    just above the credits bbox. If credits are not included, then the quote's bbox
    takes up the entire height of the screen.

    Args:
        row (dict): A single row from the CSV file.
        include_credits (bool): True to print quote's author and title, False to discard.
        pen (Pen): The pen used to write the quote.

    Returns:
        Image: An image with the quote and credits drawn on it.
    '''
    quote = row['quote']
    timestring = row['timestring']
    author = row['author']
    title = row['title']

    # mode='L' constrains the image to 8-bit grayscale
    quote_image = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)

    scale_multiplier = 0.99 # we don't want to write exactly to the edges
    quote_bbox = BoundingBox(
        top_left_x=int(SCREEN_WIDTH - SCREEN_WIDTH * scale_multiplier),
        top_left_y=int(SCREEN_HEIGHT - SCREEN_HEIGHT * scale_multiplier),
        bottom_right_x=int(SCREEN_WIDTH * scale_multiplier),
        bottom_right_y=int(SCREEN_HEIGHT * scale_multiplier)
    )

    if include_credits:
        pen.text_type = TextType.CREDITS
        pen.bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.45), # adjust the magic numbers as needed.
            top_left_y=int(SCREEN_HEIGHT * 0.85),
            bottom_right_x=int(SCREEN_WIDTH),
            bottom_right_y=int(SCREEN_HEIGHT * 0.99)
        )

        # Write the credits onto the image, then resize the quote's bbox to end just above the top
        # of the credit's bbox
        quote_credit = f'—{title.strip()}, {author.strip()}'
        pen.text = quote_credit
        write_in_bbox(quote_image, pen)
        quote_bbox.bottom_right_y = int(pen.bbox.top_left_y * 0.99) # resize to above credit bbox

    pen.bbox = quote_bbox
    pen.text = quote
    pen.text_type = TextType.QUOTE
    write_in_bbox(quote_image, pen, timestring)
    return quote_image


if __name__ == "__main__":
    default_font = ImageFont.truetype(FONT_PATH_REGULAR, 1, ImageFont.Layout.BASIC)
    my_pen = Pen(default_font, QUOTE_COLOR)

    if OUTPUT == ImageOutput.SAVE:
        try:
            if not path.exists(IMAGE_PATH):
                print('/images folder not found. Creating new folder…')
                os.mkdir(IMAGE_PATH)
        except OSError:
            print('error while trying to create /images folder')

        with open(QUOTES_PATH, newline='\n', encoding='UTF-8') as csvfile:
            num_quotes = len(csvfile.readlines()) - 1
            csvfile.seek(0) # move file cursor to start of file

            if len(argv) > 1:
                if argv[1].isdigit() and int(argv[1]) < num_quotes:
                    num_quotes = int(argv[1])

            quotereader = csv.DictReader(csvfile, delimiter='|')
            img_num = 0
            previous_time = ''
            quote_img:Image.Image
            for i, curr_row in enumerate(quotereader):
                if i >= num_quotes:
                    break

                if curr_row['time'] == previous_time:
                    img_num += 1
                else:
                    img_num = 0
                    previous_time = curr_row['time']

                time = curr_row['time'].replace(':', '')
                filepath = f'{IMAGE_PATH}quote_{time}_{img_num}.{IMAGE_FORMAT}' # e.g., images/quote_1235_2.bmp
                filepath = path.normpath(filepath)

                quote_img = generate_img(curr_row, True, my_pen)
                quote_img.save(filepath)
                progressbar = f'Creating images... {i+1}/{num_quotes}'
                print(progressbar, end='\r', flush=True)
