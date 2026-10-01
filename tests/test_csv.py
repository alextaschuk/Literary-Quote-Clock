'''Tests to validate that the quotes CSV file is formatted properly and isn't missing any info.'''
import csv
from datetime import datetime

QUOTES_PATH = 'quotes.csv'

def _get_csv_rows():
    '''Get a list of all rows from the CSV (excluding the header row).'''
    with open(QUOTES_PATH, newline="", encoding="UTF-8") as csv_file:
        return list(csv.reader(csv_file, delimiter="|"))[1:]


def _read_times():
    '''Return a list of all values from the `time` column in the quotes CSV.'''
    return [row[0] for row in _get_csv_rows()[1:]]


def _minutes_since_midnight(time:str):
    '''
    Calculate the number of minutes that have passed since midnight for a given time.

    Args:
        time (str): A string with a 24-hour time format of HH:MM.
    '''
    hour, minute = map(int, time.split(":"))
    return hour * 60 + minute


def test_every_minute_has_a_quote():
    '''
    Verify that there is at least one quote for every minute of the day (00:00–23:59).
    '''
    times = _read_times()
    minutes = {_minutes_since_midnight(t) for t in times}

    expected = set(range(24 * 60))
    missing = expected - minutes

    assert not missing, f"Missing minutes: {', '.join(f'{m // 60:02d}:{m % 60:02d}' for m in sorted(missing))}"


def test_time_format():
    '''Verify that all strings in the `time` column match the 24-hour "HH:MM format.'''
    times = _read_times()
    for row_num, time in enumerate(times):
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            assert False, f"Row {row_num}'s time column (\"{time}\") is not in the expected 24-hour HH:MM format."


def test_times_in_order():
    '''
    Verify that every value in the CSV's `time` column has either the same minute as the previous
    row's minute value, or is at most one minute greater than the previous row's minute value.
    '''
    times = _read_times()

    for row_num, (previous, current) in enumerate(zip(times, times[1:])):
        previous_minutes = _minutes_since_midnight(previous)
        current_minutes = _minutes_since_midnight(current)

        assert current_minutes in (previous_minutes, previous_minutes + 1), (
            f"Invalid time at CSV row {row_num}: {current} follows {previous} but expected \
            {previous} or the next minute")


def test_number_of_columns():
    '''Verify that all rows have the expected number of columns'''
    with open(QUOTES_PATH, newline="", encoding="UTF-8") as csv_file:
        read = csv.reader(csv_file, delimiter='|')
        EXPECTED_COLS = len(next(read)) # read number of cols from the header row

    for row_num, row in enumerate(_get_csv_rows()):
        num_cols = len(row)
        assert num_cols == EXPECTED_COLS, f"Row {row_num} has {num_cols} columns. Expected is {EXPECTED_COLS}."


def test_timestr_in_quote():
    '''
    Verify that each row has a `timestring` value that is a substring in its `quote` value.
    - This is not case-sensitive.
    '''
    for row_num, row in enumerate(_get_csv_rows()):
        timestr = row[1].lower()
        quote = row[2].lower()
        assert timestr in quote, f"Row {row_num} has missing or mismatched timestring. Expected to find: \"{timestr}\""
