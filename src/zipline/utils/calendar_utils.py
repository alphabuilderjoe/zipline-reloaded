import inspect
from functools import partial

import pandas as pd
from exchange_calendars import ExchangeCalendar as TradingCalendar
from exchange_calendars import clear_calendars
from exchange_calendars import get_calendar as ec_get_calendar  # get_calendar,
from exchange_calendars import (
    get_calendar_names,
    register_calendar,
    register_calendar_alias,
)
from exchange_calendars.calendar_utils import global_calendar_dispatcher

# from exchange_calendars.errors import InvalidCalendarName
from exchange_calendars.utils.pandas_utils import days_at_time  # noqa: reexport


# https://stackoverflow.com/questions/56753846/python-wrapping-function-with-signature
def wrap_with_signature(signature):
    def wrapper(func):
        func.__signature__ = signature
        return func

    return wrapper


@wrap_with_signature(inspect.signature(ec_get_calendar))
def get_calendar(*args, **kwargs):
    if args[0] in ["us_futures", "CMES", "XNYS", "NYSE"]:
        return ec_get_calendar(*args, side="right", start=pd.Timestamp("1990-01-01"))
    return ec_get_calendar(*args, side="right")


# get_calendar = compose(partial(get_calendar, side="right"), "XNYS")
# NOTE Sessions are now timezone-naive (previously UTC).
# Schedule columns now have timezone set as UTC
# (whilst the times have always been defined in terms of UTC,
# previously the dtype was timezone-naive).

# Add these constants at the module level (after existing imports)

# Data frequency constants
DAILY = 'daily'
MINUTE = 'minute'
FIVE_MIN = '5m'
FIFTEEN_MIN = '15m'
THIRTY_MIN = '30m'
HOURLY = '1h'
TWO_HOUR = '2h'
FOUR_HOUR = '4h'

# Valid frequencies set
VALID_DATA_FREQUENCIES = {
    DAILY, MINUTE, FIVE_MIN, FIFTEEN_MIN, 
    THIRTY_MIN, HOURLY, TWO_HOUR, FOUR_HOUR
}

# Map frequencies to minute counts
FREQUENCY_TO_MINUTES = {
    MINUTE: 1,
    FIVE_MIN: 5,
    FIFTEEN_MIN: 15,
    THIRTY_MIN: 30,
    HOURLY: 60,
    TWO_HOUR: 120,
    FOUR_HOUR: 240,
    DAILY: 390  # 6.5 hour trading day
}

# Map string representations to internal constants
FREQUENCY_STRINGS = {
    '1m': MINUTE,
    '5m': FIVE_MIN,
    '15m': FIFTEEN_MIN,
    '30m': THIRTY_MIN,
    '1h': HOURLY,
    '2h': TWO_HOUR,
    '4h': FOUR_HOUR,
    '1d': DAILY,
    # Also support the internal format
    'minute': MINUTE,
    'daily': DAILY,
    '5m': FIVE_MIN,
    '15m': FIFTEEN_MIN,
    '30m': THIRTY_MIN,
    '1h': HOURLY,
    '2h': TWO_HOUR,
    '4h': FOUR_HOUR
}

def normalize_frequency(frequency):
    """
    Convert frequency string to internal constant.
    
    Parameters
    ----------
    frequency : str
        Frequency string like '1m', '4h', '1d', 'minute', 'daily', etc.
        
    Returns
    -------
    str
        The normalized internal frequency constant.
        
    Examples
    --------
    >>> normalize_frequency('1m')
    'minute'
    >>> normalize_frequency('4h')
    '4h'
    >>> normalize_frequency('1d')
    'daily'
    """
    return FREQUENCY_STRINGS.get(frequency, frequency)