'''Contains functions for checking how a word should be formatted, if at all.
'''
from dataclasses import dataclass
from typing import Optional
import unicodedata 
from PIL import ImageFont

FONT_PATH_REGULAR = 'fonts/Bookerly.ttf'                 # non-timestring words
FONT_PATH_BOLD = 'fonts/Bookerly-Bold.ttf'               # timestring words
FONT_PATH_ITALIC = 'fonts/Bookerly-Italic.ttf'           # italicized words
FONT_PATH_ITALIC_BOLD = 'fonts/Bookerly-Bold-Italic.ttf' # italicized timestring words
FONT_PATH_CREDIT = FONT_PATH_BOLD                        # for the quote's book title and author

@dataclass
class FontType:
    '''store all of the font types'''
    regular:bool = False
    bold:bool = False
    italic:bool = False
    italic_bold:bool = False
    credit:bool = False



def format_word(word: str, is_timestr: Optional[bool]=False):
    '''checks a string for formatting chars and returns the corresponding font'''


def check_italic(word:str):
    '''Checks if the '`◻`' character is present in a word.
    Args:
        word (str): The word to check.
    Returns:
        Bool: `True` if the word should be italicized, `False` otherwise
    '''
    if '◻' in word:
        return True
    return False

def check_bold(word:str):
    '''Checks if the '`◯`' character is present in a word.
    Args:
        word (str): The word to check.
    Returns:
        Bool: `True` if the word should be bold, `False` otherwise
    '''
    if '◯' in word:
        return True
    return False

def check_new_line():
    '''TODO'''

def check_blank_line():
    '''TODO'''
