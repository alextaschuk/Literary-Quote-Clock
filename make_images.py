'''
 This is a modified version of elegantalchemist's quote_to_image.py program.
 The original can be found at 
 https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/quote_to_image.py.

 This program is used to generate .bmp images that will be displayed to the
 e-ink screen. It will automatically put the generated files into the /images
 folder in this project's root directory.
'''

# imports for image generation
from sys import argv, exit
from os import path
import os
import csv
from time import sleep
import unicodedata
from PIL import Image, ImageFont, ImageDraw

# Stuff for read and writing files
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

QUOTE_WIDTH = SCREEN_WIDTH      # the width of the quote should be 100% of the screen's width
QUOTE_HEIGHT = SCREEN_HEIGHT    # the height of the quote should be 100% of the screen's height

# note: I renamed some of the variables for personal preference.
# *{var_name} denotes the original variable names in elegantalchemist's file.

CSV_PATH = 'litclock_annotated.csv'     # the CSV file with all quotes, author names, etc. *csvpath
IMG_DIR = 'images/'                     # which directory to save images to *imgdir
IMG_EXT = 'bmp'                         # images will be in BMP format *imgformat
INCLUDE_METADATA = True                 # true = include quote's author and book title in image
imgsize = (SCREEN_WIDTH,SCREEN_HEIGHT)
BG_COLOR = 255      # set the image's background color to white (Hex = #0xFFFFFF) *color_bg
QUOTE_COLOR1 = 192  # set the text's color to light grey/silver (Hex = #0xC0C0C0) *color_norm
QUOTE_COLOR2 = 128  # set the color of the text to grey (Hex = #0x808080) *color_norm
TIME_COLOR = 0      # bold the color of the time in the quote (Hex = #0x000000, black) *color_high

QUOTE_FONT = 'fonts/Bookerly.ttf'                    # font the quote is written in *fntname_norm
ITALIC_QUOTE_FONT = 'fonts/Bookerly-Italic.ttf'      # used for italicized word(s) in the quote
ITALIC_TIME_FONT = 'fonts/Bookerly-Bold-Italic.ttf'  # used if the timestring is italicized
TIME_FONT = 'fonts/Bookerly-Bold.ttf'                # bold the timestring *fntname_high
INFO_FONT = 'fonts/Bookerly-Bold.ttf'           # font for quote's author and book *fntname_mdata
INFO_FONTSIZE = 25                              # font size for the author/title *fntsize_mdata

# don't touch
IMGNUMBER = 0
PREVIOUSTIME = ''

def turn_quote_into_image(index:int, time:str, quote:str, timestring:str, author:str, title:str):
    '''
     Defines the location on the image where text should start/stop,
     and writes the quote's metadata (author and book title) 
    '''
    global IMGNUMBER, PREVIOUSTIME
    savepath = IMG_DIR
    quoteheight = QUOTE_HEIGHT      # How far top-to-bottom the quote spans
    quotelength = QUOTE_WIDTH       # How far left-to-right the quote spans
    quotestart_y = 00               # Y coordinate where the quote begins
    quotestart_x = 10               # X coordinate where the quote begins
    mdatalength = 341               # To help with text wrapping; bigger value = longer horizontal metadata text
    mdatastart_y = 480              # Y coordinate where the author and title text begins
    mdatastart_x = 785              # X coordinate where the author and title text begins

    # create the object. mode 'L' restricts to 8bit greyscale
    paintedworld = Image.new(mode='L', size=(imgsize), color=BG_COLOR)
    ariandel = ImageDraw.Draw(paintedworld)

    # draw the title and author name
    if INCLUDE_METADATA:
        font_mdata = create_fnt(INFO_FONT, INFO_FONTSIZE)
        metadata = f'—{title.strip()}, {author.strip()}' # e.g. '—Dune, Frank Herbert
        # wrap lines into a reasonable length and lower the maximum height the
        # quote can occupy according to the number of lines the credits use
        if font_mdata.getlength(metadata) > mdatalength: # e.g. getlength(metadata) = 282.0 for '—Dune, Frank Herbert'
            metadata = wrap_lines(metadata, font_mdata, mdatalength - 23)
        for line in metadata.splitlines():
            mdatastart_y -= font_mdata.getbbox("A")[3] + 4
        quoteheight = mdatastart_y - 5
        mdata_y = mdatastart_y
        for line in metadata.splitlines():
            ariandel.text((mdatastart_x, mdata_y), line, TIME_COLOR,
                                                    font_mdata, anchor='rm')
            mdata_y += font_mdata.getbbox("A")[3] + 4
    else:
        savepath += 'nometadata/'

    # draw the quote (pretty)
    quote, fntsize = calc_fntsize(quotelength, quoteheight, quote, TIME_FONT)
    font_norm = create_fnt(QUOTE_FONT, fntsize)
    font_high = create_fnt(TIME_FONT, fntsize)
    try:
        draw_quote(drawobj=ariandel, anchors=(quotestart_x,quotestart_y), text=quote, substr=timestring, font_norm=font_norm, font_high=font_high, fntsize=fntsize)
    # warn and discard image if timestring is just not there
    except LookupError:
        print(f"WARNING: missing timestring at csv line {index+2}, skipping. ")
        return

    # increment a number if time is identical to the last one, so
    # images can't be overwritten
    # this assumes lines are actually chronological
    if time == PREVIOUSTIME:
        IMGNUMBER += 1
    else:
        IMGNUMBER = 0
        PREVIOUSTIME = time
    time = time.replace(':','')
    savepath += f'quote_{time}_{IMGNUMBER}.{IMG_EXT}'
    savepath = path.normpath(savepath)
    #image = f'quote_{time}_{IMGNUMBER}.bmp'
    #image = Image.open(img).convert('L').save(imgOut)
    paintedworld.save(savepath)

def draw_quote(drawobj, anchors:tuple, text:str, substr:str, font_norm:ImageFont.truetype, font_high:ImageFont.truetype, fntsize):
    '''
     Draws text with timestring highlighted. doesn't check if it will fit the
     image or anything else
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
        print('Error at: ' + flattened)
        raise LookupError
    substr_ends = substr_starts + len(substr)
    bookmark = '|'
    lines = text[:substr_starts]
    lines += f'{bookmark}{text[substr_starts:substr_ends]}{bookmark}'
    lines += text[substr_ends:]

    font_italic = create_fnt(ITALIC_QUOTE_FONT, fntsize)
    fntstyle_italic = (QUOTE_COLOR2, font_italic)

    font_italic_high= create_fnt(ITALIC_TIME_FONT, fntsize)
    fntstyle_italic_high = (TIME_COLOR, font_italic_high)

    fntstyle_norm = (QUOTE_COLOR2, font_norm)
    fntstyle_high = (TIME_COLOR, font_high)
    current_style = fntstyle_norm
    marks_found = 0
    write = drawobj.text
    textlength = drawobj.textlength
    x = start_x
    y = start_y

    for line in lines.splitlines():
        for word in line.split():
            word += ' '
            if '⭕' in word:
                word = word.replace('⭕', '')
                word = '    ' + word
            # if the entire time quote substr is one contiguous word, split the
            # non-substr bits stuck to it and print the whole thing in 3 parts
            if word.count(bookmark) == 2: # e.g. if word == '|◯𝘰’𝘤𝘭𝘰𝘤𝘬◯.|'
                wordnow = word.split(bookmark)[0] # word.split(bookmark) is ['', '◯𝘰’𝘤𝘭𝘰𝘤𝘬◯', '.'] so wordnow = ''
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                wordnow = word.split(bookmark)[1]  # wordnow = '◯𝘰’𝘤𝘭𝘰𝘤𝘬◯'
                if '◯' in word: # words that should be italicized and are part of the time are wrapped in this character
                    wordnow = unicodedata.normalize('NFKD', wordnow.replace('◯', '')) # get the base form (ASCII) version of the letter and remove '◯'
                    write((x,y), wordnow, *fntstyle_italic_high) # wordnow = "o'clock" and we write it with italicized & highlighted font
                    x += textlength(wordnow, font_italic_high)
                else:
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
        fontlen = font.getlength(line)
        #if font.getlength(line) <= line_length:
        if '⭐' in word:
            lines.append("")
            word = word.replace('⭐', '')
            lines.append(word)
        elif fontlen <= line_length:
            lines[-1] = line
        else:
            lines.append(word)

        return '\n'.join(lines)


def calc_fntsize(length:int, height:int, text:str, fntname:str, basesize=50, maxsize=800):
    '''
     this will dynamically wrap and scale text with the optimal font size to
     fill a given textbox, both length and height wise.
     manually setting basesize to just below the mean of a sample will
     massively reduce processing time with large batches of text, at the risk
     of potentially wasting it with strings much larger than the mean
    '''

    # these are just for calculating the textbox size, they're discarded
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
        boxheight = monalisa.multiline_textbbox((0,0), lines, fnt)[3]

    fntsize -= 1
    fnt = fnt.font_variant(size=fntsize)
    lines = wrap_lines(text, fnt, length)
    boxlength = monalisa.multiline_textbbox((0,0), lines, fnt)[2]
    while boxlength > length:
        # note: this is a sanity check. we intentionally don't reformat lines
        # here, as wrap_lines only checks if its output is *longer* than length,
        # which can produce a recursive loop where lines always get wrapped
        # into something longer, leading to overly small and unreadable fonts
        fntsize -= 1
        fnt = fnt.font_variant(size=fntsize)
        boxlength = monalisa.multiline_textbbox((0,0), lines, fnt)[2]
    # recursive call in case original basesize was too low
    boxheight = monalisa.multiline_textbbox((0,0), lines, fnt)[3]
    if boxheight > height:
        return calc_fntsize(length, height, text, fntname, basesize-5)
    return lines, fntsize


def create_fnt(name:str, size:int, layout_engine=ImageFont.Layout.BASIC):
    ''' Open and return a font file '''
    # Layout.BASIC is orders of magnitude faster than RAQM but will struggle
    # with RTL languages
    # see https://github.com/python-pillow/Pillow/issues/6631
    return ImageFont.truetype(name, size, layout_engine=layout_engine)


def main():
    ''' Call to parse CSV and generate all images '''
    try:
        if not path.exists(IMG_DIR):
            print('/images folder not found. Creating new folder...')
            os.mkdir(IMG_DIR)
    except OSError:
        print('error while trying to create /images folder')
    with open(CSV_PATH, newline='\n', encoding='UTF-8') as csvfile:
        jobs = len(csvfile.readlines()) - 1 # number of quotes in CSV file
        csvfile.seek(0) # move file cursor to start of file
        if len(argv) > 1:
            if argv[1].isdigit() and int(argv[1]) < jobs:
                jobs = int(argv[1])
        quotereader = csv.DictReader(csvfile, delimiter='|')
        for i, row in enumerate(quotereader):
            if i >= jobs:
                break
            #time = [[t.replace('\ufeff', '') for t in row] for row in csvfile]
            #if '\ufeff' in row['time']:
            #    row['time'] = row['time'].replace('\ufeff', '')
            turn_quote_into_image(i, row['time'], row['quote'], row['timestring'], row['author'], row['title'])
            progressbar = f'Creating images... {i+1}/{jobs}'
            print(progressbar, end='\r', flush=True)
    print("")

if __name__ == '__main__':
    try:
        main()
        print("Image generation complete.")
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
        exit(0)
