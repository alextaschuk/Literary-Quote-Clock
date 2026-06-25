'''module docstring'''
from dataclasses import dataclass
from enum import Enum
from typing import Any
from PIL import Image, ImageDraw, ImageFont


@dataclass
class Formatters:
    '''class docstring'''
    italic:str = '◻'
    bold:str = '◯'
    timestr:str = '|'

    def __init__(self) -> None:
        self.italic_count:int = 0
        self.bold_count:int = 0
        self.timestr_count:int = 0


class Pen:
    '''class docstring'''
    def __init__(self, font:ImageFont.FreeTypeFont, x:int=0, y:int=0, color:int=128) -> None:
        self.font = font
        self.x = x
        self.y = y
        self.color = color
        self.formatter = Formatters()

    def found_italic_delim(self, num_found:int):
        '''function docstring'''
        self.formatter.italic_count += num_found

    def found_bold_delim(self, num_found:int):
        '''function docstring'''
        self.formatter.bold_count += num_found

    def found_timestr_delim(self, num_found:int):
        '''function docstring'''
        self.formatter.timestr_count += num_found

    def reset_italic_delim(self):
        '''function docstring'''
        self.formatter.italic_count = 0

    def reset_bold_delim(self):
        '''function docstring'''
        self.formatter.bold_count = 0

    def reset_timestr_delim(self):
        '''function docstring'''
        self.formatter.timestr_count = 0

    def reset(self, x_pos:int, y_pos:int):
        '''reset the pen to the starting pos and delim counters to 0'''
        self.x = x_pos
        self.y = y_pos
        self.reset_italic_delim()
        self.reset_bold_delim()
        self.reset_timestr_delim()
