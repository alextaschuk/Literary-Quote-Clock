'''Classes and variables to handle how text is written and track where it is written.

To enable text formatting when text is written onto an image, there is a need to track the location
of the text as it is written (to ensure it is written in the correct place and does not overlap with
itself or go beyond the screen).

This module contains dataclasses that define and track delimiting characters for text formatting,
and a `Pen` class to track which font and what color to use, when writing and where to write text.
'''
from enum import Enum
from dataclasses import dataclass
from PIL import ImageFont

class TextType(Enum):
    '''Describes which part of the text is being written.'''
    QUOTE   = 1
    CREDITS = 2  # author and book title

@dataclass
class CharacterDelimiters:
    '''Stores all deliminating characters for text formatting.'''
    ITALIC  = '◻'        # U+25FB (White Medium Square)
    BOLD    = '◯'        # U+25EF (Large Circle)
    TIMESTR = '|'        # U+007C (Vertical Line)

@dataclass
class WordDelimiters:
    '''Stores delimiting characters for word formatting.'''
    NEWLINE = '⏎'        # U+23CE (Return Symbol)
    DOUBLE_NEWLINE = '⇇' # U+21C7 (Leftwards Paired Arrows)

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
    '''Defines the top left and bottom right (x,y) coordinates of a bounding box to determine
    optimal font size.
    '''
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int

    def __repr__(self) -> str:
        return f"({self.top_left_x},{self.top_left_y})({self.bottom_right_x},{self.bottom_right_y})"


class Pen:
    '''Stores info to write on an image 
    
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
    def __init__(self, font:ImageFont.FreeTypeFont, color:int):
        self.font = font
        self.color = color
        self.text_type = TextType.QUOTE
        self.text: str = ''
        self.bbox = BoundingBox(0,0,0,0)
        self.coords: dict = {'x':0, 'y':0}
        self.char_delimiters: list[Delimiter] = [ # TODO: replace with loop to iterate over class attrs and make new objs
            Delimiter(CharacterDelimiters.ITALIC),
            Delimiter(CharacterDelimiters.BOLD),
            Delimiter(CharacterDelimiters.TIMESTR)
            ]
        self.t: int


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
