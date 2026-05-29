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

def wrap_text(text:str, bbox:BoundingBox, text_type:TextType, fonts:Fonts, timestr: Optional[str] = ''):
    '''TODO'''
    words = text.split()
    lines: list[str] = [""]
    curr_line_len = 0
    total_lines_height = 0
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
            first_char_next_word = words[i + 1][0]
        else:
            word += ' '
            first_char_next_word = ' '

        # get the next word's first char to adjust for kerning.
        # see https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
        word_len = int(font.getlength(word + first_char_next_word) - font.getlength(first_char_next_word))

        # a single word cannot be longer than one line
        if word_len > bbox.bottom_right_x:
            print(f'"{word}" too long for one line')
            return None

        if curr_line_len + word_len > bbox.bottom_right_x:
            # get the current line's height before moving to the next line
            curr_line = ImageText.Text(lines[-1], font)
            line_bbox = curr_line.get_bbox()
            line_height = int(line_bbox[3] - line_bbox[1])
            total_lines_height += line_height
            if total_lines_height > bbox.bottom_right_y:
                return None

            # add the current word to a new line and reset length
            lines.append(word)
            curr_line_len = 0
        else:
            lines[-1] = f'{lines[-1]} {word}'

        curr_line_len = int(font.getlength(lines[-1]))
    return '\n'.join(lines)




def find_optimal_font_size(text:str, bbox: BoundingBox, text_type:TextType,
                           timestr: Optional[str] = '') -> int | None:
    '''Find maximum possible font size of a given bounding box
    without having to actually draw the text.

    Args:
        text (str): The text to fit inside the bounding box.
        bbox (BoundingBox): A bounding box to fill with the text.
        timestr (str): **Optional**: If passing in a quote, include the quote's timestring.

    Returns:
        int | None: The optimal font size once found, or `None` if a word is too
        long and cannot fit on one line.
    '''
    min_size = 12
    max_size = 150 if text_type == TextType.QUOTE else 45
    optimal_size = None
    longest_line = -1

    # binary search to find optimal font size
    while min_size <= max_size:
        curr_x = bbox.top_left_x
        curr_y = bbox.top_left_y
        mid_size = min_size + (max_size - min_size) // 2

        curr_words = list()
        lines = list()
        quote_words = text.split()

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

        for i, word in enumerate(quote_words):
            # TODO: replace w/ function to determine font .. also need function to check formatting.
            if timestr_begin <= i <= timestr_end:
                font = fonts.bold
            else:
                font = fonts.regular

            # get the next word's first char to adjust for kerning.
            # see https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
            if i + 1 < len(quote_words):
                next_words_first_char = quote_words[i + 1][0]
            else:
                word += ' '
                next_words_first_char = " "
            word_len = int(font.getlength(word + next_words_first_char) - font.getlength(next_words_first_char))

            # a single word cannot be longer than one line
            if word_len > bbox.bottom_right_x:
                print(f'"{word}" too long for one line')
                max_size = mid_size - 1
                break

            # move word to next line so that it's not printed off the screen
            if curr_x + word_len > bbox.bottom_right_x:
                curr_x = bbox.top_left_x

                # move to the next line on the y-axis, get the height of the current line's bbox,
                # and add it to the y axis
                line_str = ''.join(curr_words)
                curr_line = ImageText.Text(line_str, font)
                line_bbox = curr_line.get_bbox()
                line_height = int(line_bbox[3] - line_bbox[1])
                curr_y += line_height

                line_width = int(line_bbox[2] - line_bbox[0])
                if line_width > longest_line:
                    longest_line = line_width

                #if line_height > tallest_line:
                #    tallest_line = line_height
                lines.append(curr_words)
                curr_words = list()


            curr_x += word_len
            curr_words.append(word)
            if curr_y > bbox.bottom_right_y:
                max_size = mid_size - 1
            else:
                optimal_size = mid_size
                min_size = mid_size + 1

        if curr_words not in lines:
            lines.append(curr_words)
    #if tallest_line > -1:
    #    bbox.top_left_y = bbox.bottom_right_y - tallest_line

    total_height = 0
    for line in lines:
        line_str = ''.join(line)
        curr_line = ImageText.Text(line_str, font)
        line_bbox = curr_line.get_bbox()
        line_height = int(line_bbox[3] - line_bbox[1])
        total_height += line_height

        line_width = int(line_bbox[2] - line_bbox[0])
        if line_width > longest_line:
            longest_line = line_width

    bbox.top_left_x = bbox.bottom_right_x - longest_line
    bbox.top_left_y = bbox.bottom_right_y - total_height

    return optimal_size


def write_in_bbox(text:str, bbox:BoundingBox, text_type:TextType, img:Image.Image):
    '''Write a given string into a bounding box.

    Args:
        text (str): The text to write inside of the bounding box.
        bbox (BoundingBox): The bounding box that the string will fill.
        img (Image.Image): The `Image` to write the text on.
    '''
    canvas = ImageDraw.Draw(img)
    canvas.rectangle((bbox.top_left_x, bbox.top_left_y, bbox.bottom_right_x, bbox.bottom_right_y))
    canvas.rectangle((498, 384, 800, 480))
    fnt_size = find_optimal_font_size(text, bbox, text_type)
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
        #canvas.rectangle((bbox.top_left_x, bbox.top_left_y, bbox.bottom_right_x, bbox.bottom_right_y))
        #canvas.rectangle((800, 480, 801, 481))
        write = canvas.text
        quote_words = text.split()
        x = bbox.top_left_x
        y = bbox.top_left_y
        canvas = ImageDraw.Draw(img)
        font = fonts.regular
        color = QUOTE_COLOR if text_type == TextType.QUOTE else TIME_COLOR
        curr_words = list() # stores words written to the current line

        for i, word in enumerate(quote_words):
            word += " "
            # get the next word's first char to adjust for kerning.
            # see https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getlength
            if i + 1 < len(quote_words):
                next_words_first_char = quote_words[i + 1][0]
            else:
                next_words_first_char = " "

            word_len = int(font.getlength(word + next_words_first_char) - font.getlength(next_words_first_char))

            if x + word_len > bbox.bottom_right_x:
                x = bbox.top_left_x

                line_str = ''.join(curr_words)
                curr_line = ImageText.Text(line_str, font)
                line_bbox = curr_line.get_bbox()
                line_height = int(line_bbox[3] - line_bbox[1])
                y += line_height
                curr_words = list()

            write(xy=(x,y), text=word, fill=color, font=font, anchor='ls')
            curr_words.append(word)
            x += word_len
            #img.show()



def TurnQuoteIntoImage(index:int, time:str, quote:str, timestring:str, author:str, title:str, include_metadata: bool):
    '''Generate an image of a quote.

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
        quote_bbox.bottom_right_y = int(QUOTE_HEIGHT * 0.80)

        mdata_bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.55),
            top_left_y = int(SCREEN_HEIGHT * 0.80),
            #bottom_right_x = int(QUOTE_WIDTH),
            #bottom_right_y = int(QUOTE_HEIGHT)
            bottom_right_x = int(SCREEN_WIDTH),
            bottom_right_y = int(SCREEN_HEIGHT)
            )

        metadata = f'—{title.strip()}, {author.strip()}' # e.g. '—Dune, Frank Herbert
        write_in_bbox(metadata, mdata_bbox, TextType.CREDITS, quote_image)

        quote_image.show()

if __name__ == "__main__":
    time = '12:00'
    quote = 'The man crawled across a dune top. He was a mote caught in the glare of the noon sun.'
    timestr = 'noon'
    author = 'Frank Herbert'
    title = 'Dune'
    TurnQuoteIntoImage(0, time, quote, timestr, author, title, True)
