'''Classes and variables to handle how text is written and to track where it is written.

To enable text formatting when text is written onto an image, there is a need to track the location
of the text as it is written (to ensure it is written in the correct place and does not overlap with
itself or go beyond the screen).

This module contains dataclasses that define and track delimiting characters for text formatting,
and a `Pen` class to track which font and what color to use, when writing and where to write text.
'''
from dataclasses import dataclass
from enum import Enum
from PIL import ImageFont

'''Text Config'''
@dataclass
class FontPath:
    REGULAR     = 'fonts/Bookerly.ttf'                # non-timestring words
    BOLD        = 'fonts/Bookerly-Bold.ttf'           # timestring words
    ITALIC      = 'fonts/Bookerly-Italic.ttf'         # italicized words
    ITALIC_BOLD = 'fonts/Bookerly-Bold-Italic.ttf'    # italicized timestring words
    CREDIT      = BOLD # for the quote's book title and author

MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 150

class TextType(Enum):
    '''Describes which part of the text is being written.'''
    QUOTE   = 1
    CREDITS = 2  # author and book title

@dataclass
class CharacterDelimiters:
    '''Stores all deliminating characters for text formatting.
    
    Attributes:
        ITALIC (str): Text wrapped with this delimiter is written using an *italicized* version
         of the font.
        BOLD (str): Text wrapped with this delimiter is written using a **bolded** version of
         the font.
         - Note: This can be combined with the `ITALIC` delimiter to write text that is ***bold
          and italic***.
        TIMESTR (str): The timestring part of the quote is automatically wrapped with this
         delimiter.
    '''
    ITALIC  = '◻' # U+25FB (White Medium Square)
    BOLD    = '◯' # U+25EF (Large Circle)
    TIMESTR = '|' # U+007C (Vertical Line)

    def __dir__(self)->list[str]:
        '''Return a list of delimiting characters for character formatting.'''
        return [self.ITALIC, self.BOLD, self.TIMESTR]

@dataclass
class WordDelimiters:
    '''Stores delimiting characters for word formatting.
    
    Attributes:
        NEWLINE (str): Insert a newline between the current and succeeding text. (Equivalent to
         pressing the enter/return key)
        DOUBLE_NEWLINE (str): Insert two newlines between the current and succeeding text.
         (Equivalent to pressing the enter/return twice)
    '''
    NEWLINE        = '␤' # U+2424 (Symbol For Newline)
    DOUBLE_NEWLINE = '⇇' # U+21C7 (Leftwards Paired Arrows)

    def __dir__(self)->list[str]:
        '''Return a list of delimiting characters for word formatting.'''
        return [self.NEWLINE, self.DOUBLE_NEWLINE]

@dataclass
class Delimiter:
    '''Defines a formatting delimiter and stores how many of said characters have been seen in a
    text'''
    def __init__(self, character:str):
        self.character:str = character
        self.count:int = 0

@dataclass
class Fonts:
    '''Consolidates `FreeTypeFont` objects for all of the fonts that may be used to write text.'''
    regular:     ImageFont.FreeTypeFont
    bold:        ImageFont.FreeTypeFont
    italic:      ImageFont.FreeTypeFont
    italic_bold: ImageFont.FreeTypeFont
    credit:      ImageFont.FreeTypeFont


@dataclass
class BoundingBox:
    '''Defines the top left and bottom right (x,y) coordinates to constrain text when determining
    optimal font size.
    '''
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int

    def __repr__(self) -> str:
        return f"({self.top_left_x},{self.top_left_y})({self.bottom_right_x},{self.bottom_right_y})"


class Pen:
    '''Stores info to write on an image.
    
    Attributes:
        font (ImageFont.FreeTypeFont): The font that text will be written in.
        color (int): The color of the font (in RGB).
        text_type (TextType): Determines whether the pen is writing the quote or the quote's credits
         onto the image.
        text (str): The text that the pen is writing.
        bbox (BoundingBox): An area that the pen must write inside of. The bbox should be
         overwritten after a new pen is made (default coords are (0,0)(0,0)).
        coords (dict): Stores the X and Y coordinates of the pen's location on the image.
        char_delimiters (list[Delimiter]): A list of all delimiters that are used to format
         characters.
    '''
    def __init__(self):
        self.font = ImageFont.truetype(FontPath.REGULAR, MIN_FONT_SIZE, ImageFont.Layout.BASIC)
        self.color = 128
        self.text_type = TextType.QUOTE
        self.text: str = ''
        self.bbox = BoundingBox(0,0,0,0)
        self.coords: dict = {'x':0, 'y':0}
        self.char_delimiters: list[Delimiter] = [ # TODO: replace with loop to iterate over class attrs and make new objs
            Delimiter(CharacterDelimiters.ITALIC),
            Delimiter(CharacterDelimiters.BOLD),
            Delimiter(CharacterDelimiters.TIMESTR)
            ]


    def reset(self, x_pos:int, y_pos:int):
        '''Move the pen and set all delimiter counters to 0.
        
        Args:
            x_pos (int): The X coordinate to move the pen to.
            y_pos (int): The Y coordinate to move the pen to.
        '''
        self.coords['x'] = x_pos
        self.coords['y'] = y_pos
        for delimiter in self.char_delimiters:
            delimiter.count = 0
