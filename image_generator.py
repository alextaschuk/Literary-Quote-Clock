'''
Generate an image of a quote and either:
(a) Save it as a file
(b) Return it as an Image.Image object
'''
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from pen import Pen, ITALIC, BOLD, TIMESTR, QUOTE_COLOR, TIME_COLOR, reset_delim

logging.basicConfig(level=logging.DEBUG)


class ImageOutput(Enum):
    '''Determine what `generate_img()` should do with each generated image: save it to an /images
    folder, or return an `Image` object.
    '''
    SAVE   = 1  # save images to an /images folder
    RETURN = 2  # return an Image object from TurnQuoteIntoImage()


class TextType(Enum):
    '''Describes which part of a quote is being passed into a function.'''
    QUOTE   = 1
    CREDITS = 2  # author and book title of the quote


@dataclass
class BoundingBox:
    '''Defines the top left and bottom right (x,y) coordinates of a bounding box to determine
    optimal font size.
    '''
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int


@dataclass
class Fonts:
    '''Consolidates `FreeTypeFont` objects for all of the fonts that may be used.'''
    regular: ImageFont.FreeTypeFont
    bold: ImageFont.FreeTypeFont
    italic: ImageFont.FreeTypeFont
    italic_bold: ImageFont.FreeTypeFont
    credit: ImageFont.FreeTypeFont


# screen config
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 480

# image config
OUTPUT      = ImageOutput.RETURN  # should the main function save an image, or return it?
QUOTE_PATH  = 'quotes.csv'
BG_COLOR    = 255   # image's background color is white (#0xFFFFFF)


# for a list of all image formats that Pillow supports, see
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#fully-supported-formats
IMAGE_FORMAT = 'bmp'

# paths to font files
FONT_PATH_REGULAR       = 'fonts/Bookerly.ttf'        # non-timestring words
FONT_PATH_BOLD          = 'fonts/Bookerly-Bold.ttf'      # timestring words
FONT_PATH_ITALIC        = 'fonts/Bookerly-Italic.ttf'  # italicized words
FONT_PATH_ITALIC_BOLD   = 'fonts/Bookerly-Bold-Italic.ttf' # italicized timestring words
FONT_PATH_CREDIT        = FONT_PATH_BOLD # for the quote's book title and author

MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 150


def get_word_len(words: list[str], curr_word_len:int, curr_word: str, curr_word_pos: int, num_words: int,
                 font: ImageFont.FreeTypeFont):
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
        next_word = words[curr_word_pos + 1]
        next_word_pen = Pen(font)

        fonts = Fonts(
            regular=ImageFont.truetype(FONT_PATH_REGULAR, font.size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FONT_PATH_BOLD, font.size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FONT_PATH_ITALIC, font.size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, font.size, ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FONT_PATH_CREDIT, font.size, ImageFont.Layout.BASIC)
        )
        #temp_next = next_word
        next_first_char = next_word[0]
        next_first_char = check_font(next_first_char, fonts, next_word_pen)

        #next_word_first_char = temp_next[0]
        #curr_word += ' '
        #curr_word_len = font.getlength(curr_word)
        #next_first_char_len = next_word_pen.font.getlength(next_word_first_char)
        next_first_char_len = next_word_pen.font.getlength(next_first_char)
        return int(curr_word_len + next_first_char_len) - int(next_first_char_len)

    # current word is the last word of the text
    first_char_next_word = ''
    # TODO: replace this kind of stuff to return default values (float) as late as possible for max accuracy. then convert to int
    return int(font.getlength(curr_word + first_char_next_word) - font.getlength(first_char_next_word))


def check_font(char: str, fonts: Fonts, pen: Pen):
    '''Determine which font the pen should use to write a word.
    This updates the pen's font and color. If the word has any delimiting
    characters, they are removed and the word is returned.
    '''
    italic_count = 0
    found_delimiter = False
    for delimiter in pen.delimiters:
        if char == delimiter.delim_char:
            found_delimiter = True
            delimiter.count += 1
            char = ''
        if delimiter.count == 1:
            found_delimiter = True
            pen.color = delimiter.text_color
            if delimiter.delim_char == ITALIC:
                italic_count = delimiter.count
                pen.font = fonts.italic
            if delimiter.delim_char == BOLD or delimiter.delim_char == TIMESTR:
                pen.font = fonts.italic_bold if italic_count > 0 else fonts.bold

    if not found_delimiter:
        pen.font = fonts.regular
        pen.color = QUOTE_COLOR

    return char


def draw_word(img: Image.Image, words: list[str], word: str, word_pos: int, fonts: Fonts, pen: Pen):
    '''function docstring'''
    canvas = ImageDraw.Draw(img)
    write = canvas.text
    for char in word:
        char = check_font(char, fonts, pen)
        if char == '':
            continue
        write((pen.x, pen.y), char, pen.color, pen.font)
        pen.x += int(pen.font.getlength(char))

    # add a space after each word
    write((pen.x, pen.y), ' ', pen.color, pen.font)
    pen.x += int(pen.font.getlength(' '))
    #word = check_font(word, fonts, pen)
    #for delimiter in pen.delimiters:
    #    if len(delimiter.delim_positions) > 0:
    #        if delimiter.count == 1:
    #            delim_idx = delimiter.delim_positions[0]
    #            curr_word = word[:delim_idx]
    #            temp_font = pen.font
    #            pen.font = fonts.regular
    #            word_len = get_word_len(words, curr_word, word_pos, len(words), pen.font)
    #            write((pen.x, pen.y), curr_word, pen.color, pen.font)
    #            pen.x += word_len
    #            pen.font = temp_font
    #            curr_word = word[delim_idx:]
    #            word_len = get_word_len(words, curr_word, word_pos, len(words), pen.font)
    #            write((pen.x, pen.y), curr_word, pen.color, pen.font)
    #            pen.x += word_len
    #        elif delimiter.count == 2:
    #            pass

    #word_len = get_word_len(words, word, word_pos, len(words), pen.font)
    #write((pen.x, pen.y), word, pen.color, pen.font)
    #pen.x += word_len

    #reset_font = False
    for delimiter in pen.delimiters:
        if delimiter.count >= 2:
            reset_delim(delimiter)
            pen.font = fonts.regular
            #reset_font = True
    #if reset_font:
        #pen.font = fonts.regular


def wrap_text(text: str, bbox: BoundingBox, fonts: Fonts, pen: Pen, timestr: Optional[str] = '') -> str:
    '''Helper to `find_optimal_font_size()`. Wraps text so that it doesn't overflow past the
    rightmost x coordinate of the bbox.
    '''
    lines: list[str] = [""]
    pen.x = bbox.top_left_x
    pen.y = bbox.top_left_y
    # iterate over the text word-by-word and try to place each word on the current line. If the word
    # cannot fit, move down one line and place it there instead.
    words = text.split()
    for i, word in enumerate(words):
        temp_word = word
        word_len = 0
        for char_pos, char in enumerate(temp_word):
            char = check_font(char, fonts, pen)
            if char == '':
                continue
            word_len += pen.font.getlength(char)

        #word_len = get_word_len(words, word_len, temp_word, i, len(words), pen.font)

        # a single word cannot be longer than one line
        if word_len > bbox.bottom_right_x - bbox.top_left_x:
            pen.reset(bbox.top_left_x, bbox.top_left_y)
            return ''
        
        word_len += int(pen.font.getlength(' '))

        if pen.x + word_len > bbox.bottom_right_x:
            # move to the next line, add the current word to the line, and reset x coord
            # TODO: Replace with get_lineheight()
            pen.y += int(pen.font.getbbox("A")[3] + 4)
            lines.append(word)
            pen.x = bbox.top_left_x
        else:
            # add the current word to the current line
            lines[-1] = f'{lines[-1]} {word}'
        pen.x += word_len

        # current wrapping writes text past bbox (need to reduce font size)
        if pen.y > bbox.bottom_right_y:
            pen.reset(bbox.top_left_x, bbox.top_left_y)
            return ''

    wrapped = '\n'.join(lines)

    # verify that the wrapping fits
    # TODO figure out how pillow calculates bbox and manually implement height calculation so that i dont have to make all of these objects each time
    temp_img = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)
    canvas = ImageDraw.Draw(temp_img)
    pil_bbox = canvas.multiline_textbbox((bbox.top_left_x, bbox.top_left_y), wrapped, fonts.regular)

    if pil_bbox[3] > bbox.bottom_right_y:
        pen.reset(bbox.top_left_x, bbox.top_left_y)
        return ''
    return wrapped


def find_optimal_font_size(text: str, bbox: BoundingBox, text_type: TextType,
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

    inital_font = ImageFont.truetype(FONT_PATH_REGULAR, min_size, ImageFont.Layout.BASIC)
    temp_pen = Pen(font=inital_font)

    # binary search to find optimal font size
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
        lines = wrap_text(text, bbox, fonts, temp_pen, timestr)
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


def write_in_bbox(text: str, bbox: BoundingBox, text_type: TextType, img: Image.Image, pen: Pen,
                  timestr: Optional[str] = ""):
    '''Write a given string into a bounding box.

    Args:
        text (str): The text to write inside of the bounding box.
        bbox (BoundingBox): The bounding box that the string will fill.
        img (Image.Image): The Image to write the text on.
        timestr (Optional[str]): A substring that contains the quote's time.
    '''
    # wrap the timestr with '|' so that we can find it again when drawing each word.
    timestr_begin, timestr_end = -1, -1
    if timestr:
        try:
            timestr_begin = text.lower().index(timestr.lower())
            timestr_end = timestr_begin + len(timestr)
            temp_words = text[:timestr_begin]
            temp_words += f'{TIMESTR}{text[timestr_begin:timestr_end]}{TIMESTR}'
            temp_words += text[timestr_end:]
            text = temp_words
        except ValueError as exc:
            logging.error('Timestring doesn\'t match or isn\'t found in quote ("%s...")', text[:10])
            raise LookupError from exc

    pen.font.size, wrapped_lines = find_optimal_font_size(text, bbox, text_type, timestr)
    print(f'optimal fontsize: {pen.font.size}')

    if pen.font.size <= MIN_FONT_SIZE:
        raise ValueError(
            f'Error: Text "{text}" is too long and doesn’t fit in bbox {bbox}.')

    fonts = Fonts(
        regular=ImageFont.truetype(FONT_PATH_REGULAR, pen.font.size, ImageFont.Layout.BASIC),
        bold=ImageFont.truetype(FONT_PATH_BOLD, pen.font.size, ImageFont.Layout.BASIC),
        italic=ImageFont.truetype(FONT_PATH_ITALIC, pen.font.size, ImageFont.Layout.BASIC),
        italic_bold=ImageFont.truetype(FONT_PATH_ITALIC_BOLD, pen.font.size, ImageFont.Layout.BASIC),
        credit=ImageFont.truetype(FONT_PATH_CREDIT, pen.font.size, ImageFont.Layout.BASIC)
    )

    pen.color = QUOTE_COLOR if text_type == TextType.QUOTE else TIME_COLOR
    pen.y = bbox.top_left_y
    print('starting to draw')
    for line in wrapped_lines.splitlines():
        pen.x = bbox.top_left_x
        words = line.split()
        for i, word in enumerate(words):
            draw_word(img, words, word, i, fonts, pen)
        # TODO: Replace with get_lineheight()
        pen.y += int(pen.font.getbbox("A")[3] + 4)


def generate_img(index: int, time: str, quote: str, timestring: str, author: str, title: str,
                 include_credits: bool, pen: Pen):
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
    quote_image = Image.new(mode='L', size=(
        SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)

    scale_multiplier = 0.99 # we don't want to write exactly to the edges
    quote_bbox = BoundingBox(
        top_left_x=int(SCREEN_WIDTH - SCREEN_WIDTH * scale_multiplier),
        top_left_y=int(SCREEN_HEIGHT - SCREEN_HEIGHT * scale_multiplier),
        bottom_right_x=int(SCREEN_WIDTH * scale_multiplier),
        bottom_right_y=int(SCREEN_HEIGHT * scale_multiplier)
    )

    if include_credits:
        cred_bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.45),
            top_left_y=int(SCREEN_HEIGHT * 0.85),
            bottom_right_x=int(SCREEN_WIDTH),
            bottom_right_y=int(SCREEN_HEIGHT * 0.99)
        )

        # Write the credits onto the image, then resize the quote's bbox to just above the
        # top of the credit's bbox (e.g. '—Dune, Frank Herbert)
        quote_credit = f'—{title.strip()}, {author.strip()}'
        write_in_bbox(quote_credit, cred_bbox, TextType.CREDITS, quote_image, pen)
        quote_bbox.bottom_right_y = int(cred_bbox.top_left_y * 0.99)

    write_in_bbox(quote, quote_bbox, TextType.QUOTE, quote_image, pen, timestring)
    quote_image.show()


if __name__ == "__main__":
    #TIME = '12:00'
    #QUOTE = 'The man crawled across a dune top. He was a mote caught in the glare of the noon sun.'
    #TIMESTRING = 'noon'
    #AUTHOR = 'Frank Herbert'
    #TITLE = 'Dune'

    TIME = '06:21'
    #QUOTE = "The whipped mules dragged the wagon on through a flooded branch that submerged thirty yards of the road and stood up around the bushes and tree-trunks on either side so that they had no rootage, and I watched where and how deep the wheels went while I idled the motor and lighter Gudger's and my own cigarette. It was twenty-one past six."
    QUOTE = "It’s twenty-◻one◻ ◻past◻ six. This B◻◯is◻a◯n, test, string."
    TIMESTRING = "twenty-◻one◻ ◻past◻ six"
    AUTHOR = "James Agee and Walker Evans"
    TITLE = 'Let Us Now Praise Famous Men'

    #TIME='02:00'
    #QUOTE='Henry held out his hand for the note, which Victoria gave over in exchange for a Sweet Caporal. There were only four words: ◻Tomorrow morning. 2 o’clock◻.'
    #TIMESTRING='2 o’clock'
    #TITLE='Full Dark, No Stars'
    #AUTHOR='Stephen King'

    default_font = ImageFont.truetype(FONT_PATH_REGULAR, 1, ImageFont.Layout.BASIC)
    my_pen = Pen(font=default_font)
    generate_img(0, TIME, QUOTE, TIMESTRING, AUTHOR, TITLE, include_credits=True, pen=my_pen)
