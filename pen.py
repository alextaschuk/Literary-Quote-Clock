'''module docstring'''
from dataclasses import dataclass
from enum import Enum
from PIL import Image, ImageDraw, ImageFont


@dataclass
class Formatters:
    '''class docstring'''
    italic: str = '◻'
    bold: str = '◯'
    timestr: str = '|'

    italic_count: int = 0
    bold_count: int = 0
    timestr_count: int = 0

class FormatDelimiter(Enum):
    '''class docstring'''
    ITALIC = 1
    BOLD = 2
    TIMESTR = 3


class Pen:
    '''class docstring'''
    formatter = Formatters()
    def __init__(self, font: ImageFont.FreeTypeFont, x: int, y: int) -> None:
        self.font = font
        self.fontsize = font.size
        self.x = x
        self.y = y

    def found_italic_delim(self):
        '''function docstring'''
        self.formatter.italic_count += 1

    def found_bold_delim(self):
        '''function docstring'''
        self.formatter.bold_count += 1

    def found_timestr_delim(self):
        '''function docstring'''
        self.formatter.timestr_count += 1

    def reset_italic_delim(self):
        '''function docstring'''
        self.formatter.italic_count = 0

    def reset_bold_delim(self):
        '''function docstring'''
        self.formatter.bold_count = 0

    def reset_timestr_delim(self):
        '''function docstring'''
        self.formatter.timestr_count = 0
