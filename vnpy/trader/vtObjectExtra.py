from vnpy.trader.vtConstant import EMPTY_STRING

class VtCandlesQueryData(object):
    def __init__(self):
        self.symbol = EMPTY_STRING # 合约代码
        self.vtSymbol = EMPTY_STRING # 合约在vt系统中的唯一代码
        self.granularity = None # Bar数据粒度(频率)，必填
        self.start = None  # Bar数据起始时间，python的datetime对象可选
        self.end = None # Bar数据结束时间，可选
        self.size =  None # Bar数据长度，可选

    @classmethod
    def new(cls, symbol, granularity, size=None, start=None, end=None):
        obj = cls() 
        obj.symbol = symbol
        obj.granularity = granularity
        obj.size = size
        obj.start = start
        obj.end = end
        return obj


class VtCandlesData(object):
    def __init__(self):
        self.meta = None # VtCandlesQueryData
        self.data = None # pandas.DataFrame contains bar data, with datetime field as index.
