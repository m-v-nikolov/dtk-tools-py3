import platform

import pytz
from pytz import timezone


def get_os():
    """
    Retrieve OS
    """

    sy = platform.system()

    # OS: windows
    if sy == 'Windows':
        my_os = 'win'
    # OS: Linux
    elif sy == 'Linux':
        my_os = 'lin'
    # OS: Mac
    else:
        my_os = 'mac'

    return my_os


def utc_to_local(utc_dt):
    local_tz = timezone('US/Pacific')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt) # .normalize might be unnecessary