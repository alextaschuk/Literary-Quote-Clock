'''module docstring'''
# rename to writer.py
from dataclasses import dataclass
from PIL import ImageFont

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

@ dataclass
class Delimiter:
    '''class docstring'''
    def __init__(self, delimiter:str, color:int) -> None:
        self.delim_char:str = delimiter
        self.count:int = 0
        self.delim_positions:list[int] = []
        self.text_color:int = color

ITALIC = '◻'
BOLD = '◯'
TIMESTR = '|'

QUOTE_COLOR = 128   # non-timestring text is grey (#0x808080)
TIME_COLOR  = 0     # timestring text is black (#0x000000)


class Pen:
    '''class docstring'''
    def __init__(self, font:ImageFont.FreeTypeFont, x:int=0, y:int=0, color:int=128) -> None:
        self.font = font
        self.x = x
        self.y = y
        self.color = color
        self.delimiters:list[Delimiter] = [
                                           Delimiter(ITALIC, QUOTE_COLOR),
                                           Delimiter(BOLD, TIME_COLOR),
                                           Delimiter(TIMESTR, TIME_COLOR)
                                           ]

    def reset(self, x_pos:int, y_pos:int):
        '''reset the pen to the starting pos and delim counters to 0'''
        self.x = x_pos
        self.y = y_pos
        for delimiter in self.delimiters:
            reset_delim(delimiter)

def found_delim(delimiter:Delimiter, num_found:int):
    '''function docstring'''
    delimiter.count += num_found

def reset_delim(delimiter:Delimiter):
    '''function docstring'''
    delimiter.count = 0
    delimiter.delim_positions = []

    #def found_italic_delim(self, num_found:int):
    #    '''function docstring'''
    #    self.formatter.italic_count += num_found

    #def found_bold_delim(self, num_found:int):
    #    '''function docstring'''
    #    self.formatter.bold_count += num_found

    #def found_timestr_delim(self, num_found:int):
    #    '''function docstring'''
    #    self.formatter.timestr_count += num_found

    #def reset_italic_delim(self):
    #    '''function docstring'''
    #    self.formatter.italic_count = 0

    #def reset_bold_delim(self):
    #    '''function docstring'''
    #    self.formatter.bold_count = 0

    #def reset_timestr_delim(self):
    #    '''function docstring'''
    #    self.formatter.timestr_count = 0

    #def reset(self, x_pos:int, y_pos:int):
    #    '''reset the pen to the starting pos and delim counters to 0'''
    #    self.x = x_pos
    #    self.y = y_pos
    #    self.reset_italic_delim()
    #    self.reset_bold_delim()
    #    self.reset_timestr_delim()
