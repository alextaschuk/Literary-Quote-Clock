'''
 This is a modified version of elegantalchemist's quote_to_image.py program. The original file can be
 found at https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/quote_to_image.py.

 My modified version will generate .bmp files to be displayed on Waveshare's 7.5 inch
 E-ink display. To generate the .bmp files, I parse a CSV file that contains the quotes
 Some other changes include the color of the image, and the font.

 Things that come from elegantalchemist that I modified:
    image generation program
    csv file with quotes

    I used this csv file https://github.com/JohannesNE/literature-clock/blob/master/litclock_annotated.csv 
    instead of elegantalchemist's as it seemed more refined and has more quotes.
'''

# imports for image generation
from sys import argv, exit
from os import path
import csv
csv.field_size_limit(100000000)
from PIL import Image, ImageFont, ImageDraw
from time import sleep
import unicodedata


# Stuff for read and writing files
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

QUOTE_WIDTH = SCREEN_WIDTH                      # the width (length) of the quote should be 100% of the screen's width
QUOTE_HEIGHT = SCREEN_HEIGHT * .90              # the height of the quote should be 90% of the screen's height
 
# note: I renamed some of the variables for personal preference. *{var_name} denotes the original variable names in elegantalchemist's file.
csv_path = 'litclock_annotated.csv'             # the CSV file with all quotes, author names, etc. *csvpath
img_dir = 'images/'                             # which directory to save images to *imgdir
img_ext = 'bmp'                                 # images will be in BMP format *imgformat
include_metadata = True                         # true = include the author and book's title of the quote
imgsize = (SCREEN_WIDTH,SCREEN_HEIGHT)
bg_color = 255                                  # set the image's background color to white (Hex equivalent is #0xFFFFFF) *color_bg
quote_color1 = 192                              # set the color of text to light grey/silver (Hex equivalent is #0xC0C0C0) *color_norm
quote_color2 = 128                              # set the color of the text to grey (Hex equivalent is #0x808080) *color_norm
time_color = 0                                  # bold the color of the time in the quote (Hex equivalent is #0x000000, black) *color_high

quote_font = 'Bookerly.ttf'                     # the font the quote will be written in *fntname_norm
italic_quote_font = 'Bookerly-Italic.ttf'       # used if word(s) in the quote are italicized
bold_italic_quote_font = 'Bookerly-Bold-Italic.tff'  # used if the time part of quote is also italicized
time_font = 'Bookerly-Bold.ttf'                 # bold version of quote_font (for time part of quote) *fntname_high
info_font = 'Bookerly-Bold.ttf'                 # the font the book and Author's name will be written in *fntname_mdata
info_fontsize = 25                              # the font size for the author/title *fntsize_mdata

# don't touch
imgnumber = 0
previoustime = ''

def TurnQuoteIntoImage(index:int, time:str, quote:str, timestring:str,
                                               author:str, title:str):
    global imgnumber, previoustime
    savepath = img_dir
    quoteheight = QUOTE_HEIGHT      # How far top-to-bottom the quote spans
    quotelength = QUOTE_WIDTH       # How far left-to-right the quote spans
    quotestart_y = 00               # Y coordinate where the quote begins
    quotestart_x = 10               # X coordinate where the quote begins
    mdatalength = 341               # To help with text wrapping
    mdatastart_y = 480              # Y coordinate where the author and title text begins
    mdatastart_x = 785              # X coordinate where the author and title text begins

    # create the object. mode 'L' restricts to 8bit greyscale
    paintedworld = Image.new(mode='L', size=(imgsize), color=bg_color)
    ariandel = ImageDraw.Draw(paintedworld)

    # draw the title and author name
    if include_metadata:
        font_mdata = create_fnt(info_font, info_fontsize)
        metadata = f'—{title.strip()}, {author.strip()}'
        # wrap lines into a reasonable length and lower the maximum height the
        # quote can occupy according to the number of lines the credits use
        if font_mdata.getlength(metadata) > mdatalength:
            metadata = wrap_lines(metadata, font_mdata, mdatalength - 23)
        for line in metadata.splitlines():
            mdatastart_y -= font_mdata.getbbox("A")[3] + 4
        quoteheight = mdatastart_y - 10
        mdata_y = mdatastart_y
        for line in metadata.splitlines():
            ariandel.text((mdatastart_x, mdata_y), line, time_color,
                                                    font_mdata, anchor='rm')
            mdata_y += font_mdata.getbbox("A")[3] + 4
    else:
        savepath += 'nometadata/'

    # draw the quote (pretty)
    quote, fntsize = calc_fntsize(quotelength, quoteheight, quote, time_font)
    font_norm = create_fnt(quote_font, fntsize)
    font_high = create_fnt(time_font, fntsize)
    try:
        draw_quote(drawobj=ariandel, anchors=(quotestart_x,quotestart_y), text=quote, substr=timestring, font_norm=font_norm, font_high=font_high, fntsize=fntsize)
    # warn and discard image if timestring is just not there
    except LookupError:
        print(f"WARNING: missing timestring at csv line {index+2}, skipping")
        return

    # increment a number if time is identical to the last one, so
    # images can't be overwritten
    # this assumes lines are actually chronological
    if time == previoustime:
        imgnumber += 1
    else:
        imgnumber = 0
        previoustime = time
    time = time.replace(':','')
    savepath += f'quote_{time}_{imgnumber}.{img_ext}'
    savepath = path.normpath(savepath)
    #image = f'quote_{time}_{imgnumber}.bmp'
    #image = Image.open(img).convert('L').save(imgOut)
    paintedworld.save(savepath)
    sleep(0.2) # sleep for 0.2 seconds to help ensure no images get skipped

def draw_quote(drawobj, anchors:tuple, text:str, substr:str,
        font_norm:ImageFont.truetype, font_high:ImageFont.truetype, fntsize):
    # draws text with substr highlighted. doesn't check if it will fit the
    # image or anything else
    start_x = anchors[0]
    start_y = anchors[1]

    # search for the substring as if text were a single line, and
    # mark its starting and ending position for the upcoming write loop
    flattened = text.replace('\n',' ')
    substr_starts = 0
    try:
        substr_starts = flattened.lower().index(substr.lower())
    except ValueError:
        raise LookupError
    substr_ends = substr_starts + len(substr)
    bookmark = '|'
    lines = text[:substr_starts]
    lines += f'{bookmark}{text[substr_starts:substr_ends]}{bookmark}'
    lines += text[substr_ends:]

    fntstyle_norm = (quote_color2, font_norm)
    fntstyle_high = (time_color, font_high)
    current_style = fntstyle_norm
    marks_found = 0
    write = drawobj.text
    textlength = drawobj.textlength
    x = start_x
    y = start_y

    line_list = lines.splitlines()
    for line in line_list:
        for word in line.split():
            # We need to check if a character italicized, and if it is, the font needs to change.
            # However, the font won't print italicized characters (i.e., the letters in the
            # string itself are italicized), so we need to convert them to normal characters.
            # There are two solutions that I can think of right now, but they're both imperfect. 
            # The first one (which is currently) being used only skips substrings that have a 
            # charcter that's in the chars_to_skip array. However, this causes undesirable results.
            
            # For example, the substring "and 𝘵𝘳𝘪𝘴𝘵𝘦𝘴𝘴𝘦." results in the '.' char also being 
            # italicized becaues the unicode value for a full stop (.) isn't in chars_to_skip. 
  
            # The other solution is to add the full stop to chars_to_skip, but this results in 
            # "𝘵𝘳𝘪𝘴𝘵𝘦𝘴𝘴𝘦" not being italicized. I need to figure out how to separate the full stop 
            # character from the rest of the italicized substring.
            if not word.isascii():
                if word[0] == " ":
                    word.replace()
                for letter in word:
                    chars_to_skip = [233, 8212, 8217, 8220, 8221,] #latin small letter E with acute, em dash, right single quotation mark, left double quotation mark, right double quotation mark,
                    if ord(letter) in chars_to_skip:
                        #word = word.replace(letter, "")
                        if letter == word[0] or letter == word[len(word) - 1]:
                            font_norm = create_fnt(quote_font, fntsize)
                            font_high = create_fnt(time_font, fntsize)
                            fntstyle_norm = (quote_color2, font_norm)
                            fntstyle_high = (time_color, font_high)
                            current_style = fntstyle_norm
                            break
                        else:
                            new_word = " " + word[word.index(letter):len(word)] 
                            line = line[:line.index(word) + len(word)] + new_word + line[line.index(word) + len(word):]
                            #line = line.replace(word, new_word)
                            #line_list.insert((line_list.index(line) + 1), new_word)
                            word = word.replace(new_word, "") #remove from current string
                            font_norm = create_fnt(quote_font, fntsize)
                            font_high = create_fnt(time_font, fntsize)
                            fntstyle_norm = (quote_color2, font_norm)
                            fntstyle_high = (time_color, font_high)
                            current_style = fntstyle_norm
                        break
                    elif word == substr: # check if the time part of the quote is italicized
                        font_high = create_fnt(bold_italic_quote_font, fntsize)
                        fntstyle_high = (time_color, font_high)
                        current_style = fntstyle_norm
                    elif word != substr:
                        font_norm = create_fnt(italic_quote_font, fntsize) # otherwise it's just italicized
                        fntstyle_norm = (quote_color2, font_norm)
                        current_style = fntstyle_norm

                    if not(letter.isascii()):
                        word = word.replace(letter, unicodedata.normalize('NFKD', letter)) # get the base form (ASCII) version of the letter
            else:
                    font_norm = create_fnt(quote_font, fntsize)
                    font_high = create_fnt(time_font, fntsize)
                    fntstyle_norm = (quote_color2, font_norm)
                    fntstyle_high = (time_color, font_high)
                    current_style = fntstyle_norm

            word += ' '
            # if the entire substr is one contiguous word, split the
            # non-substr bits stuck to it and print the whole thing in 3 parts
            if word.count(bookmark) == 2:
                wordnow = word.split(bookmark)[0]
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                wordnow = word.split(bookmark)[1]
                write((x,y), wordnow, *fntstyle_high)
                x += textlength(wordnow, font_high)
                wordnow = word.split(bookmark)[2]
                write((x,y), wordnow, *fntstyle_norm)
                x += textlength(wordnow, font_norm)
                word = ''
            # otherwise change the default font, and wait for the next mark
            elif word.count(bookmark) == 1:
                marks_found += 1
                wordnow = word.split(bookmark)[0]
                word = word.split(bookmark)[1]
                write((x,y), wordnow, *current_style)
                x += textlength(wordnow, current_style[1])
                if marks_found == 1:
                    current_style = fntstyle_high
                else: # if marks == 2:
                    current_style = fntstyle_norm
            # this is the bit that actually does most of the writing
            write((x,y), word, *current_style)
            x += textlength(word, current_style[1])
        # the offset calculated by multiline_text (what we're trying to mimic)
        # is based on uppercase letter A plus 4 pixels for some reason.
        # See https://github.com/python-pillow/Pillow/discussions/6620
        y += font_norm.getbbox("A")[3] + 4
        x = start_x


def wrap_lines(text:str, font:ImageFont.truetype, line_length:int):
    # wraps lines to maximize the number of words within line_length. note
    # that lines *can* exceed line_length, this is intentional, as text looks
    # better if the font is rescaled afterwards. adapted from Chris Collett
    # https://stackoverflow.com/a/67203353/8225672
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return '\n'.join(lines)


def calc_fntsize(length:int, height:int, text:str, fntname:str, basesize=50,
                                                              maxsize=800):
    # this will dynamically wrap and scale text with the optimal font size to
    # fill a given textbox, both length and height wise.
    # manually setting basesize to just below the mean of a sample will
    # massively reduce processing time with large batches of text, at the risk
    # of potentially wasting it with strings much larger than the mean

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
    # Layout.BASIC is orders of magnitude faster than RAQM but will struggle
    # with RTL languages
    # see https://github.com/python-pillow/Pillow/issues/6631
    return ImageFont.truetype(name, size, layout_engine=layout_engine)


def main():
    with open(csv_path, newline='\n', encoding='UTF-8') as csvfile:
        jobs = len(csvfile.readlines()) - 1
        csvfile.seek(0)
        if len(argv) > 1:
            if argv[1].isdigit() and int(argv[1]) < jobs:
                jobs = int(argv[1])
        quotereader = csv.DictReader(csvfile, delimiter='|')
        for i, row in enumerate(quotereader):
            if i >= jobs:
                break
            else:
                #time = [[t.replace('\ufeff', '') for t in row] for row in csvfile]
                #if '\ufeff' in row['time']:
                #    row['time'] = row['time'].replace('\ufeff', '')
                TurnQuoteIntoImage(i, row['time'],row['quote'],
                row['timestring'], row['author'], row['title'])
            progressbar = f'Creating images... {i+1}/{jobs}'
            print(progressbar, end='\r', flush=True)
    print("")


if __name__ == '__main__':
    try:
        main()
        sleep(60) # sleep for 1 minute to ensure all images finish processing in the background
        print("Image generation complete.")
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
        exit(0)
