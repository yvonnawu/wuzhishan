from enum import Enum

import numpy as np
import numpy.lib.recfunctions as rfn
import pandas as pd
from vnpy.trader.utils.datetime import dt2int

from ...ctaTemplate import ArrayManager as OriginArrayManager

default_size = 100

class DatetimeIntArrayManager(OriginArrayManager):
    def __init__(self, size=default_size):
        super(DatetimeIntArrayManager, self).__init__(size=size)
        dt_int = np.array([(0,)]*size, dtype=np.dtype([('datetimeint', np.int64)]))
        self.array = rfn.merge_arrays([dt_int, self.array], flatten=True, usemask=False)
        self._count = 0
        self._inited = False
        self._size = size

    def updateBar(self, bar):
        if bar:
            super(DatetimeIntArrayManager, self).updateBar(bar)
            self.array['datetimeint'][0:self.size - 1] = self.array['datetimeint'][1:self.size]
            self.array['datetimeint'][-1] = dt2int(bar.datetime)

    @property
    def head(self):
        return max(0, self.size - self.count)

    @property
    def datetimeint(self):
        return self.array["datetimeint"]

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, v):
        self._size = v

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, v):
        self._count = v

    @property
    def inited(self):
        return self.count >= self.size
    
    @inited.setter
    def inited(self, v):
        self._inited = v


class ArrayManagerWithUncomplete(DatetimeIntArrayManager):
    class UPDATE_METHOD(Enum):
        INSERT = "insert"
        MERGE = "merge"
        OVERRIDE = "override"
    
    def __init__(self, size):
        super(ArrayManagerWithUncomplete, self).__init__(size=size+1)
        self._end_time = None
        self._complete = True
    
    @property
    def complete(self):
        return self._complete

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, v):
        self._end_time = v

    def updateBar(self, bar, method="insert", end_time=None, complete=None):
        method = self.UPDATE_METHOD(method)
        if method == self.UPDATE_METHOD.INSERT:
            complete = True if complete is None else complete  # For insert, assume updated bar is complete
            super(ArrayManagerWithUncomplete, self).updateBar(bar)
        else:
            complete = False if complete is None else complete # For others, assume updated bar is uncomplete
            if method == self.UPDATE_METHOD.MERGE:
                self.array["high"][-1] = max(self.array["high"][-1], bar.high)
                self.array["low"][-1] = min(self.array["low"][-1], bar.low)
            else:
                self.array["high"][-1] = bar.high
                self.array["low"][-1] = bar.low
            self.array["open"][-1] = bar.open
            self.array["close"][-1] = bar.close
            self.array["datetime"][-1] = bar.datetime.strftime(self.DATETIME_FORMAT)
            self.array["datetimeint"][-1] = dt2int(bar.datetime)
        self._end_time = end_time or self._end_time
        self._complete = complete


class ArrayManager(ArrayManagerWithUncomplete):
    def __init__(self, size=default_size):
        super(ArrayManager, self).__init__(size=size)
        self._end_time_complete = None
        self._updating = False

    def updateBar(self, bar, method="insert", end_time=None, complete=None):
        self._updating = True
        self.uncomplete.updateBar(bar, method=method, end_time=end_time, complete=complete)
        self._updating = False
        if complete:
            self._end_time_complete = end_time or self._end_time_complete

    @property
    def uncomplete(self):
        return super(ArrayManager, self)

    def _get_slice(self):
        if self.uncomplete.complete:
            return slice(1, None, None)                
        else:
            return slice(None, -1, None)

    def to_dataframe(self):
        """提供DataFrame"""
        return pd.DataFrame(self.array[:][self._get_slice()])

    @property
    def datetimeint(self):
        return self.uncomplete.datetimeint[self._get_slice()]

    @property
    def datetime(self):
        return self.uncomplete.datetime[self._get_slice()]

    @property
    def open(self):
        return self.uncomplete.open[self._get_slice()]

    @property
    def high(self):
        return self.uncomplete.high[self._get_slice()]

    @property
    def low(self):
        return self.uncomplete.low[self._get_slice()]

    @property
    def close(self):
        return self.uncomplete.close[self._get_slice()]

    @property
    def complete(self):
        return True

    @property
    def size(self):
        if self._updating:
            return self.uncomplete.size
        else:
            return self.uncomplete.size - 1

    @size.setter
    def size(self, v):
        self._size = v

    @property
    def count(self):
        if self.uncomplete.complete:
            return self.uncomplete.count
        else:
            return self.uncomplete.count - 1

    @count.setter
    def count(self, v):
        self._count = v
