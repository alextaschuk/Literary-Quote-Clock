'''Classes and variables to handle how text is written and track where it is written.

To enable text formatting when text is written onto an image, there is a need to track the location
of the text as it is written (to ensure it is written in the correct place and does not overlap with
itself or go beyond the screen).

This module contains global variables that define delimiting characters for text formatting, a
`Delimiter` class to manage delimiters, and a `Pen` class to track which font and what color to use,
when writing and where to write text.
'''
from dataclasses import dataclass
from PIL import ImageFont

# delimiter characters
ITALIC = '◻'
BOLD = '◯'
TIMESTR = '|'


@dataclass
class Delimiter:
    '''Defines a formatting delimiter and stores how many of said characters have been seen in a
    text'''
    def __init__(self, delim_char:str):
        self.delim_char:str = delim_char
        self.count:int = 0


@dataclass
class Fonts:
    '''Consolidates `FreeTypeFont` objects for all of the fonts that may be used.'''
    regular: ImageFont.FreeTypeFont
    bold: ImageFont.FreeTypeFont
    italic: ImageFont.FreeTypeFont
    italic_bold: ImageFont.FreeTypeFont
    credit: ImageFont.FreeTypeFont


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
        x (int): The X coordinate of the pen's location on the image.
        y (int): The Y coordinate of the pen's location on the image.
    '''
    def __init__(self, font:ImageFont.FreeTypeFont, color:int, x:int=0, y:int=0):
        self.font = font
        self.color = color
        self.x = x
        self.y = y
        self.delimiters:list[Delimiter] = [Delimiter(ITALIC), Delimiter(BOLD), Delimiter(TIMESTR)]

    def reset(self, x_pos:int, y_pos:int):
        '''Move the pen and set all delimiter counters to 0.
        
        Args:
            x_pos (int): The X coordinate to move the pen to.
            y_pos (int): The Y coordinate to move the pen to.
        '''
        self.x = x_pos
        self.y = y_pos
        for delimiter in self.delimiters:
            delimiter.count = 0
