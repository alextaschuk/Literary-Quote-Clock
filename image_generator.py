'''
Generate an image of a quote and either save it as a file or return it as an `Image.Image` object.

To save all of the quote images to an /images folder, run this file. To return an `Image.Image`
object for a single quote, import the `generate_img()` function into your file and call it as
needed.

TODO:
- add logic to split credits into two lines
- write tests
- (for future) match delimiters to markdown (will need to handle instances where, e.g., * is
actually used) -- can use one delim for bold and italic. just track total number seen. if
num % 2 == 0 then bold otherwise italic if num > 0
- add check if quote has any formatting at all. if not, write entire quote word-by-word instead.
- find better delim chars for ~~newline~~ and double newline
- the quote and the credits because the text wrapper only really checks for horizontal wrapping,
so sometimes a quote fits better horizontally, but a bigger font may be usable if wrapping is
used earlier. Figure out a way to wrap text that takes horizontal and vertical wrapping into
consideration. Another (worse) option is to resize the credit bbox to just above the bottom of
the quote's text, after drawing the quote, giving it more space. Maybe check if there is 1 line
of space between the quote and credit bboxes. If there is, wrap the last word of the first line
onto the second line, pushing everything down by one... but this would force you to reduce
fontsize by at least 1... so idk. or increase fontsize by 1 and reduce the bbox size?
    - See "And you keep quiet, Betty..." (02:48). The credit bbox is also weird for this quote.
- Not sure that the newline delim is working properly when calculating fontsize
    - E.g., try `09:08|09:08:35 a.m.|◻09:08:35 a.m.◻ ␤WHEN MARK WAS SHOT ␤◻I was shattered. Shifted. ␤Never the same again.◻|Long Way Down|Jason Reynolds`
'''
import csv
import logging
import os
from os import path
from sys import argv
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from constants import QUOTE_COLOR, TIME_COLOR, BG_COLOR, IMAGE_FORMAT, INCLUDE_CREDITS
from constants import QUOTES_PATH, IMAGE_PATH
from constants import MIN_FONT_SIZE, MAX_FONT_SIZE

from writer import BoundingBox
from writer import CharacterDelimiters
from writer import Fonts
from writer import FontPath
from writer import Pen
from writer import TextType
from writer import WordDelimiters

logging.basicConfig(level=logging.DEBUG)


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
            return ''
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
        word_len (int): The length (in pixels) of the text (**NOT** `len(word)`!!)
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

    if pen.coords['x'] + word_len > pen.bbox.bottom_right_x or add_line:
        # move to the next line, add the current word to the line, and reset x coord
        # TODO: Replace with get_lineheight()
        pen.coords['y'] += int(pen.font.getbbox("A")[3] + 4)
        lines.append(word)
        pen.coords['x'] = pen.bbox.top_left_x
    else:
        # add the current word to the current line
        lines[-1] = f'{lines[-1]} {word}'


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

    # Iterate over the text character-by-character and try to place each word on the current line.
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
    # TODO: figure out how pillow calculates bbox and manually implement height calculation so that
    # I dont have to make all of these objects each time
    temp_img = Image.new(mode='L', size=(SCREEN_WIDTH, SCREEN_HEIGHT), color=BG_COLOR)
    canvas = ImageDraw.Draw(temp_img)
    pil_bbox = canvas.multiline_textbbox((pen.bbox.top_left_x, pen.bbox.top_left_y), wrapped, fonts.regular)

    if pil_bbox[3] > pen.bbox.bottom_right_y:
        pen.reset(pen.bbox.top_left_x, pen.bbox.top_left_y)
        return ''
    return wrapped


def find_optimal_font_size(text: str, bbox: BoundingBox, text_type: TextType) -> tuple[int, str]:
    '''Find the maximum possible font size that the text can be written in for a given bounding box.

    Args:
        text (str): The text to fit inside the bounding box.
        bbox (BoundingBox): A bounding box to fill with the text.
        text_type (TextType): Tells the function if the text is a quote or credits.

    Returns:
        tuple ([int, str]): If a valid font size is found, the tuple contains the optimal font size
        and a string containing the text broken up with newline delimiters to fit in the bbox
        horizontally. If the text cannot fit in the bbox with a font size >= `MIN_FONT_SIZE`, the
        tuple contains `[0, '']`.
    '''
    min_size = MIN_FONT_SIZE
    max_size = MAX_FONT_SIZE
    optimal_size = 0
    best_fit_lines = ""

    temp_pen = Pen()
    temp_pen.bbox = bbox
    temp_pen.text = text

    # use binary search to find optimal font size
    while min_size <= max_size:
        mid_size = min_size + (max_size - min_size) // 2
        lines = ""

        fonts = Fonts(
            regular=ImageFont.truetype(FontPath.REGULAR, mid_size, ImageFont.Layout.BASIC),
            bold=ImageFont.truetype(FontPath.BOLD, mid_size, ImageFont.Layout.BASIC),
            italic=ImageFont.truetype(FontPath.ITALIC, mid_size, ImageFont.Layout.BASIC),
            italic_bold=ImageFont.truetype(FontPath.ITALIC_BOLD, mid_size, ImageFont.Layout.BASIC),
            credit=ImageFont.truetype(FontPath.CREDIT, mid_size, ImageFont.Layout.BASIC)
        )
        temp_pen.font = fonts.regular
        lines = wrap_text(text, fonts, temp_pen)
        if lines:
            optimal_size = mid_size
            min_size = mid_size + 1
            best_fit_lines = lines
        else:  # text didn't fit
            max_size = mid_size - 1

    lines_height = 0 # sum of all lines
    line_width = 0 # length of the longest line.
    for line in best_fit_lines.splitlines():
        # TODO: Replace with get_lineheight()
        lines_height += int(fonts.regular.getbbox("A")[3] + 4)
        curr_line_width = int(fonts.regular.getlength(line))
        if curr_line_width > line_width:
            line_width = curr_line_width

    # Resize the credit bbox so to give the quote bbox the most space possible to write with.
    if text_type == TextType.CREDITS:
        bbox.top_left_y = bbox.bottom_right_y - lines_height
        bbox.top_left_x = bbox.bottom_right_x - line_width
    return (optimal_size, best_fit_lines)


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

def find_timestr_indices(pen:Pen, timestr: str):
    '''Find the indices where the timestring begins and ends in the quote.'''
    timestr_begin = pen.text.lower().index(timestr.lower())
    timestr_end = timestr_begin + len(timestr)
    return (timestr_begin, timestr_end)


def write_in_bbox(img: Image.Image, pen: Pen, timestr: Optional[str] = ""):
    '''Write text inside of a bounding box.

    Args:
        img (Image.Image): The Image to write the text on.
        pen (Pen): The pen used to write the quote.
        timestr (Optional[str]): A substring that contains the quote's time.

    Raises:
        ValueError: `timestr` is passed in by the caller, but is not present in the quote.
    '''
    # Wrap the timestr with '|' so that we can find it again when drawing each word.
    # Write an error message instead if the timestring isn't found.
    if pen.text_type == TextType.QUOTE and timestr:
        timestr_begin, timestr_end = -1, -1
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


    optimal_fontsize, wrapped_lines = find_optimal_font_size(pen.text, pen.bbox, pen.text_type)

    if optimal_fontsize <= MIN_FONT_SIZE:
        bbox_repr = repr(pen.bbox)
        logging.error('Text starting with "%s..." is too long and doesn\'t fit in bbox=%s with' \
        'minimum font=%i', pen.text[:30], bbox_repr, MIN_FONT_SIZE)

    fonts = Fonts(
        regular=ImageFont.truetype(FontPath.REGULAR, optimal_fontsize, ImageFont.Layout.BASIC),
        bold=ImageFont.truetype(FontPath.BOLD, optimal_fontsize, ImageFont.Layout.BASIC),
        italic=ImageFont.truetype(FontPath.ITALIC, optimal_fontsize, ImageFont.Layout.BASIC),
        italic_bold=ImageFont.truetype(FontPath.ITALIC_BOLD, optimal_fontsize, ImageFont.Layout.BASIC),
        credit=ImageFont.truetype(FontPath.CREDIT, optimal_fontsize, ImageFont.Layout.BASIC)
    )

    pen.coords['y'] = pen.bbox.top_left_y
    for line in wrapped_lines.splitlines():
        pen.coords['x'] = pen.bbox.top_left_x
        words = line.split()
        for word in words:
            draw_word(img, word, fonts, pen)
        # TODO: Replace with get_lineheight()
        pen.coords['y'] += int(pen.font.getbbox("A")[3] + 4)


def generate_img(row:dict, include_credits:bool, pen:Pen) -> Image.Image:
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
        quote_image (Image.Image): An image with the quote and credits drawn on it.
    '''
    quote = row['quote']
    timestring = row['timestring']
    title = row['title']
    author = row['author']

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
        # Write the credits onto the image, then resize the quote's bbox to end just above the top
        # of the credit's bbox
        pen.text_type = TextType.CREDITS
        pen.bbox = BoundingBox(
            top_left_x=int(SCREEN_WIDTH * 0.45), # adjust these magic numbers as needed.
            top_left_y=int(SCREEN_HEIGHT * 0.85),
            bottom_right_x=int(SCREEN_WIDTH),
            bottom_right_y=int(SCREEN_HEIGHT * 0.99)
        )

        quote_credit = f'—{title.strip()}, {author.strip()}'
        pen.text = quote_credit
        write_in_bbox(quote_image, pen)
        quote_bbox.bottom_right_y = int(pen.bbox.top_left_y * 0.99) # resize to above credit bbox

    pen.bbox = quote_bbox
    pen.text = quote
    pen.text_type = TextType.QUOTE
    write_in_bbox(quote_image, pen, timestring)
    pen.reset(pen.bbox.top_left_x, pen.bbox.top_left_y) # reset for the next img

    # Uncomment if images are being generated for a Kindle! The images need to be physically rotated
    # to display on the screen properly.
    #quote_image = quote_image.transpose(method=Image.Transpose.ROTATE_270)

    return quote_image


if __name__ == "__main__":
    my_pen = Pen()

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

            quote_img = generate_img(curr_row, INCLUDE_CREDITS, my_pen)
            quote_img.save(filepath)
            progressbar = f'Creating images... {i+1}/{num_quotes}'
            print(progressbar, end='\r', flush=True)
    print('Image generation complete.\r\n')
