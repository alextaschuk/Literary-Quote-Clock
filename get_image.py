'''
 This is a modified version of elegantalchemist's quote_to_image.py program. The original file can be
 found at https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/quote_to_image.py.

 This program is used to generate .bmp images that will be displayed to the e-ink screen.
 The `TurnQuoteToImage()` function is called by the `get_image()` function in `clock.py`.
 '''

from PIL import Image, ImageFont, ImageDraw
import unicodedata
import logging

logging.basicConfig(level=logging.DEBUG)

# Stuff for read and writing files
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

QUOTE_WIDTH = SCREEN_WIDTH * 0.975                     
QUOTE_HEIGHT = SCREEN_HEIGHT * 0.917
 
# note: I renamed some of the variables for personal preference. *{var_name} denotes the original variable names in elegantalchemist's file.
csv_path = 'quotes.csv'             # the CSV file with all quotes, author names, etc. *csvpath
imgsize = (SCREEN_WIDTH,SCREEN_HEIGHT)
bg_color = 255                                  # set the image's background color to white (Hex equivalent is #0xFFFFFF) *color_bg
quote_color1 = 192                              # set the color of text to light grey/silver (Hex equivalent is #0xC0C0C0) *color_norm
quote_color2 = 128                              # set the color of the text to grey (Hex equivalent is #0x808080) *color_norm
time_color = 0                                  # bold the color of the time in the quote (Hex equivalent is #0x000000, black) *color_high

quote_font = 'fonts/Bookerly.ttf'                     # the font the quote will be written in *fntname_norm
italic_quote_font = 'fonts/Bookerly-Italic.ttf'       # used if word(s) in the quote are italicized
italic_time_font = 'fonts/Bookerly-Bold-Italic.ttf'   # used if the time part of quote is also italicized
time_font = 'fonts/Bookerly-Bold.ttf'                 # bold version of quote_font (for time part of quote) *fntname_high
info_font = 'fonts/Bookerly-Bold.ttf'                 # the font the book and Author's name will be written in *fntname_mdata
info_fontsize = 30                                    # the font size for the author/title *fntsize_mdata

# don't touch
imgnumber = 0
previoustime = ''

def TurnQuoteIntoImage(index:int, time:str, quote:str, timestring:str, author:str, title:str, include_metadata: bool):
    '''
    The main function to generate an image of a quote. 
    - Returns an `Image` object
    '''
    global imgnumber, previoustime
    quoteheight = QUOTE_HEIGHT      # How far top-to-bottom the quote spans
    quotelength = QUOTE_WIDTH       # How far left-to-right the quote spans
    quotestart_y = 00               # Y coordinate where the quote begins
    quotestart_x = 20               # X coordinate where the quote begins
    mdatalength = 650               # To help with text wrapping -- bigger value = longer horizontal metadata text
    mdatastart_y = 485 # Y coordinate where the author and title text begins (should be around size of screen's height)
    mdatastart_x = SCREEN_WIDTH * 0.981  # X coordinate where the author and title text begins

    # create the object. mode 'L' restricts to 8bit greyscale
    paintedworld = Image.new(mode='L', size=(imgsize), color=bg_color)
    ariandel = ImageDraw.Draw(paintedworld)

    # first, we want to check that there are no errors with the quote
    # If there is, replace the quote with an error message to display
    temp_flattened = quote.replace('\n',' ')
    try:
        temp = temp_flattened.lower().index(timestring.lower())
    except ValueError:
        logging.error(f'Error: The timestring was not found in the quote.\n The quote throwing the error is: {temp_flattened} \nIts substr is: {timestring}')

        # create an error message to display instead and update necessary values
        quote = f'Error: Quote that begins with ⭐{quote[:10]} ⭐does not have a matching timestring.'
        timestring = 'Error'
        include_metadata = False

    if include_metadata:
        # draw the title and author name
        font_mdata = create_fnt(info_font, info_fontsize)
        metadata = f'—{title.strip()}, {author.strip()}' # e.g. '—Dune, Frank Herbert
        # wrap lines into a reasonable length and lower the maximum height the
        # quote can occupy according to the number of lines the credits use        
        if font_mdata.getlength(metadata) > mdatalength: # e.g. getlength(metadata) = 282.0 for '—Dune, Frank Herbert'
            metadata = wrap_lines(text=metadata, font=font_mdata, line_length=(mdatalength * 0.965))

        for line in metadata.splitlines():
            mdatastart_y -= font_mdata.getbbox("A")[3] + 4

        quoteheight = mdatastart_y - 25
        mdata_y = mdatastart_y

        for line in metadata.splitlines():
            ariandel.text((mdatastart_x, mdata_y), line, time_color, font_mdata, anchor='rm')
            mdata_y += font_mdata.getbbox("A")[3] + 4

    # draw the quote (pretty)
    quote, fntsize = calc_fntsize(length=quotelength, height=quoteheight, text=quote, fntname=time_font)
    font_norm = create_fnt(name=quote_font, size=fntsize)
    font_high = create_fnt(name=time_font, size=fntsize)
    try:
        draw_quote(drawobj=ariandel, anchors=(quotestart_x,quotestart_y), text=quote, substr=timestring, font_norm=font_norm, font_high=font_high, fntsize=fntsize)
    # warn and discard image if timestring is just not there
    except LookupError:
        logging.error(f"WARNING: missing timestring at csv line {index+2}, skipping")

    return paintedworld

def draw_quote(drawobj, anchors:tuple, text:str, substr:str,
        font_norm:ImageFont.truetype, font_high:ImageFont.truetype, fntsize):
    '''
    This function draws the quote with the timestring highlighted to the
    `drawobj` object that is passed in the function header. It will format
    the quote (i.e., check for italics, etc.), but it does not check if the
    quote will fit in the image or anything else.
    
    This function accepts (requires) the following arguments:
    - `drawobj`: An `ImageDraw` obj
    - `anchors`: A tuple containing the x and y starting coordinates for the quote
    - `text`: The quote
    - `substr`: The timestring of the quote (i.e., the part that should be highlighted)
    - `font_norm`: A `FreeTypeFont` obj containing the quote's font
    - `font_high`: A `FreeTypeFont` obj containing the quote's bolded font (for highlighting the time)
    - `fntsize`: A value returned from `calc_fntsize()` that determines how large the text should be
    '''

    start_x = anchors[0]
    start_y = anchors[1]

    # search for the substring as if text were a single line, and
    # mark its starting and ending position for the upcoming write loop
    flattened = text.replace('\n',' ')
    substr_starts = 0
    try:
        substr_starts = flattened.lower().index(substr.lower())
    except ValueError:
        logging.error(f'Error: The timestring (substr) was not found in the quote (text).\n The quote throwing the error is: {flattened} \nIts substr is: {substr}')

    substr_ends = substr_starts + len(substr)
    bookmark = '|'
    lines = text[:substr_starts]
    lines += f'{bookmark}{text[substr_starts:substr_ends]}{bookmark}'
    lines += text[substr_ends:]

    font_italic = create_fnt(italic_quote_font, fntsize)
    fntstyle_italic = (quote_color2, font_italic)

    font_italic_high= create_fnt(italic_time_font, fntsize)
    fntstyle_italic_high = (time_color, font_italic_high)

    fntstyle_norm = (quote_color2, font_norm)
    fntstyle_high = (time_color, font_high)
    current_style = fntstyle_norm
    marks_found = 0
    write = drawobj.text
    textlength = drawobj.textlength
    x = start_x
    y = start_y
    for line in lines.splitlines():
        for word in line.split():
            word += ' '
            # if the entire time substr is one contiguous word, split the
            # non-substr bits stuck to it and print the whole thing in 3 parts
            if word.count(bookmark) == 2: # e.g. if word == '|◯𝘰’𝘤𝘭𝘰𝘤𝘬◯.|'
                wordnow = word.split(bookmark)[0] # word.split(bookmark) is ['', '◯𝘰’𝘤𝘭𝘰𝘤𝘬◯', '.'], so wordnow = ''
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                wordnow = word.split(bookmark)[1]  # wordnow = '◯𝘰’𝘤𝘭𝘰𝘤𝘬◯'
                write((x,y), wordnow, *fntstyle_high) # if the word is normal but part of time quote, just write it with highlighted font
                x += textlength(wordnow, font_high)
                wordnow = word.split(bookmark)[2] # wordnow = '.'
                write((x,y), wordnow, *fntstyle_norm) # write wordnow with normal font
                x += textlength(wordnow, font_norm)
                word = ''
            # otherwise change the default font, and wait for the next mark
            # i.e., cases where the time quote has multiple words in it
            elif word.count(bookmark) == 1:
                marks_found += 1
                wordnow = word.split(bookmark)[0]
                if '◯' in wordnow:
                        wordnow = unicodedata.normalize('NFKD', wordnow.replace('◯', '')) 
                        current_style = fntstyle_italic_high # bold & italicized font
                word = word.split(bookmark)[1]
                write((x,y), wordnow, *current_style)
                x += textlength(wordnow, current_style[1])
                if marks_found == 1:
                    if '◯' in word:
                        word = unicodedata.normalize('NFKD', word.replace('◯', ''))
                        current_style = fntstyle_italic_high # bold & italicized font            
                    else:  
                        current_style = fntstyle_high # bold font
                else: # if marks == 2:
                    current_style = fntstyle_norm # normal font
            if '◻' in word: # words that should be fully italicized (but NOT part of time quote) are wrapped in this character
                wordnow = word.split('◻')[0]
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                wordnow = unicodedata.normalize('NFKD', word.split('◻')[1])
                write((x,y), wordnow, *fntstyle_italic)
                x += textlength(wordnow, font_italic)
                wordnow = word.split('◻')[2]
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                word = ''
            elif '◯' in word:
                wordnow = word.split('◯')[0]
                write((x,y), wordnow, *fntstyle_high)
                x += textlength(wordnow, font_high)
                wordnow = unicodedata.normalize('NFKD', word.split('◯')[1])
                write((x,y), wordnow, *fntstyle_italic_high)
                x += textlength(wordnow, font_italic_high)
                wordnow = word.split('◯')[2]
                write((x,y), wordnow, *fntstyle_high)
                x += textlength(wordnow, font_high)
                word = ''
            else: 
                write((x,y), word, *current_style)
                x += textlength(word, current_style[1])
        # the offset calculated by multiline_text (what we're trying to mimic)
        # is based on uppercase letter A plus 4 pixels for some reason.
        # See https://github.com/python-pillow/Pillow/discussions/6620
        y += font_norm.getbbox("A")[3] + 4
        x = start_x


def wrap_lines(text:str, font:ImageFont.truetype, line_length:int):
        '''
         wraps lines to maximize the number of words within line_length. note
         that lines *can* exceed line_length, this is intentional, as text looks
         better if the font is rescaled afterwards. adapted from Chris Collett
         https://stackoverflow.com/a/67203353/8225672
        '''
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            temp_line = line
            fontlen = font.getlength(line)

            # to accurately wrap lines without including delimiting
            # chars in the calculation
            if '◻' in temp_line:
                temp_line = temp_line.replace('◻', '')
                fontlen = font.getlength(temp_line)
            if '◯' in temp_line:
                temp_line = temp_line.replace('◯', '')
                fontlen = font.getlength(temp_line)

            if '⭐' in word: # the quote is formatted with a blank line between two lines of text
                word = word.replace('⭐', '')
                lines.append('')
                lines.append(word)
            elif '📖' in word: # the quote is formatted with a linebreak
                word = word.replace('📖', '')
                lines.append(word)

            # this just ensures text doesn't overflow
            elif fontlen <= line_length: 
                lines[-1] = line
            else:
                lines.append(word) # this puts the next set of text on a new line
  
        return '\n'.join(lines)


def calc_fntsize(length:int, height:int, text:str, fntname:str, basesize=50,
                                                              maxsize=480):
    '''
     this will dynamically wrap and scale text with the optimal font size to
     fill a given textbox, both length and height wise.
     manually setting basesize to just below the mean of a sample will
     massively reduce processing time with large batches of text, at the risk
     of potentially wasting it with strings much larger than the mean
     these are just for calculating the textbox size, they're discarded
    ''' 
    louvre = Image.new(mode='1', size=(0,0))
    monalisa = ImageDraw.Draw(louvre)

    lines = ''
    fntsize = basesize
    fnt = create_fnt(fntname, fntsize)
    boxheight = 0
    while not boxheight > height and not fntsize > maxsize:
        fntsize += 1
        fnt = fnt.font_variant(size=fntsize)
        lines = wrap_lines(text, fnt, length)

        # "Returns bounding box (in pixels) of given text relative to given anchor
        # when rendered in font with provided direction, features, and language.
        # Only supported for TrueType fonts." - pillow docs
        boxheight = get_boxsize(monalisa, (0,0), lines, fnt, 3)

    fntsize -= 1
    fnt = fnt.font_variant(size=fntsize)
    lines = wrap_lines(text, fnt, length)
    boxlength = get_boxsize(monalisa, (0,0), lines, fnt, 2)
    while boxlength > length:
        # note: this is a sanity check. we intentionally don't reformat lines
        # here, as wrap_lines only checks if its output is *longer* than length,
        # which can produce a recursive loop where lines always get wrapped
        # into something longer, leading to overly small and unreadable fonts
        fntsize -= 1
        fnt = fnt.font_variant(size=fntsize)
        boxlength = get_boxsize(monalisa, (0,0), lines, fnt, 2)
    # recursive call in case original basesize was too low
    boxheight = get_boxsize(monalisa, (0,0), lines, fnt, 3)
    if boxheight > height:
        return calc_fntsize(length, height, text, fntname, basesize-5)
    return lines, fntsize


def create_fnt(name:str, size:int, layout_engine=ImageFont.Layout.BASIC):
    # Layout.BASIC is orders of magnitude faster than RAQM but will struggle
    # with RTL languages
    # see https://github.com/python-pillow/Pillow/issues/6631
    return ImageFont.truetype(name, size, layout_engine=layout_engine)

def get_boxsize(image_draw_obj: ImageDraw, coords:tuple[float, float], text: str, font: ImageFont.truetype, index: int):
    '''
    This is a function to accurately calculate `boxheight` & `boxlength`
    for `calc_fntsize()` without including italic delimiting characters.
    '''
    if '◻' in text:
        text = text.replace('◻', '')
    if '◯' in text:
        text = text.replace('◯', '')
    return image_draw_obj.multiline_textbbox(coords, text, font)[index]
