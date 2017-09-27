import logging
import threading
import warnings

import pandas as pd

logger = logging.getLogger(__name__)

lock = threading.Lock()

class sample_selection:
    def __init__(self, start_date='1/1/2000', freq='W'):
        self.start_date = start_date
        self.freq = freq

    def __call__(self, timeseries):
        # N.B. once-per-period snapshots, not period-sliding-window averages...
        freq_days = {'W': 7, 'M': 30, 'D': 1, 'Y': 365}
        freq_sliced = timeseries[::freq_days[self.freq.upper()]]
        try:
            # pd.date_range appears not to be thread-safe (Issue #100)
            # time.sleep(random.random())  # workaround?!
            with lock:
                dates = pd.date_range(self.start_date, periods=len(freq_sliced), freq=self.freq)
        except ValueError:
            logger.debug('freq_sliced:\n%s', freq_sliced)
            logger.info('freq = %s', self.freq)
            logger.info('periods = %d', len(freq_sliced))
            raise
        return pd.Series(freq_sliced, index=dates)


class summary_interval_selection:
    def __init__(self, start_date='1/1/2000', freq='W'):
        self.start_date = start_date
        self.freq = freq

    def __call__(self, timeseries):
        dates = pd.date_range(self.start_date, periods=len(timeseries), freq=self.freq)
        return pd.Series(timeseries, index=dates)


def default_select_fn(ts):
    return pd.Series(ts)