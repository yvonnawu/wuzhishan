# encoding: UTF-8

import time

from vnpy.event import *

from vnpy.trader.vtEvent import *
from vnpy.trader.vtConstant import *
from vnpy.trader.vtObject import *

########################################################################
class VtGateway(object):
    """交易接口"""

    #----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName):
        """Constructor"""
        self.eventEngine = eventEngine
        self.gatewayName = gatewayName
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """市场行情推送"""
        # 通用事件
        event1 = Event(type_=EVENT_TICK)
        event1.dict_['data'] = tick
        self.eventEngine.put(event1)
        
        # 特定合约代码的事件
        event2 = Event(type_=EVENT_TICK+tick.vtSymbol)
        event2.dict_['data'] = tick
        self.eventEngine.put(event2)
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """成交信息推送"""
        # 通用事件
        event1 = Event(type_=EVENT_TRADE)
        event1.dict_['data'] = trade
        self.eventEngine.put(event1)
        
        # 特定合约的成交事件
        event2 = Event(type_=EVENT_TRADE+trade.vtSymbol)
        event2.dict_['data'] = trade
        self.eventEngine.put(event2)        
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """订单变化推送"""
        # 通用事件
        event1 = Event(type_=EVENT_ORDER)
        event1.dict_['data'] = order
        self.eventEngine.put(event1)
        
        # 特定订单编号的事件
        event2 = Event(type_=EVENT_ORDER+order.vtOrderID)
        event2.dict_['data'] = order
        self.eventEngine.put(event2)
    
    #----------------------------------------------------------------------
    def onPosition(self, position):
        """持仓信息推送"""
        # 通用事件
        event1 = Event(type_=EVENT_POSITION)
        event1.dict_['data'] = position
        self.eventEngine.put(event1)
        
        # 特定合约代码的事件
        event2 = Event(type_=EVENT_POSITION+position.vtSymbol)
        event2.dict_['data'] = position
        self.eventEngine.put(event2)
    
    #----------------------------------------------------------------------
    def onAccount(self, account):
        """账户信息推送"""
        # 通用事件
        event1 = Event(type_=EVENT_ACCOUNT)
        event1.dict_['data'] = account
        self.eventEngine.put(event1)
        
        # 特定合约代码的事件
        if account.vtAccountID:
            event2 = Event(type_=EVENT_ACCOUNT+account.vtAccountID)
            event2.dict_['data'] = account
            self.eventEngine.put(event2)
    
    #----------------------------------------------------------------------
    def onError(self, error):
        """错误信息推送"""
        # 通用事件
        event1 = Event(type_=EVENT_ERROR)
        event1.dict_['data'] = error
        self.eventEngine.put(event1)    
        
    #----------------------------------------------------------------------
    def onLog(self, log):
        """日志推送"""
        # 通用事件
        event1 = Event(type_=EVENT_LOG)
        event1.dict_['data'] = log
        self.eventEngine.put(event1)
        
    #----------------------------------------------------------------------
    def onContract(self, contract):
        """合约基础信息推送"""
        # 通用事件
        event1 = Event(type_=EVENT_CONTRACT)
        event1.dict_['data'] = contract
        self.eventEngine.put(event1)        
    
    #----------------------------------------------------------------------
    def connect(self):
        """连接"""
        pass
    
    #----------------------------------------------------------------------
    def subscribe(self, subscribeReq):
        """订阅行情"""
        pass
    
    #----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        pass
    
    #----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        pass
    
    #----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        pass
    
    #----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        pass
    #-----------------------------------
    def qryOrder(self):
        """查询特定订单"""
        pass
    #----------------------------------------------------------------------
    def close(self):
        """关闭"""
        pass

from functools import partial
from copy import copy
from concurrent.futures import Future

class ExtendedVtGateway(VtGateway):
    @property
    def now():
        """由Gateway中传递的各种消息包含的交易所时间信息确定的最新时间"""
        return None

    def qryCandlesAsync(self, req, callback=None):
        """异步获取Bar数据并调用回调函数"""
        pass

    def qryCandles(self, req, block=False, callback=None, timeout=30):
        """ 查询Bar数据,可以选择阻塞和非阻塞两种模式
        
        Parameters
        ----------
        req : [type]
            [description]
        block : bool, optional
            [description] (the default is False, which [default_description])
        callback : [type], optional
            [description] (the default is None, which [default_description])
        timeout : int, optional
            [description] (the default is 30, which [default_description])
        
        Returns
        -------
        [type]
            [description]
        """
        def set_future_result(fut, candles):
            fut.set_result(candles)
        req = copy(req)
        req.vtSymbol = VN_SEPARATOR.join([req.symbol, self.gatewayName])
        if not block:
            if callback:
                self.qryCandlesAsync(req, callback=callback)
            else:
                self.qryCandlesAsync(req, callback=self.onQryCandles)
        else:
            # if you want to use block mode, callback of qryCandlesAsync must be execute in 
            # other thread than event engine's thread.
            fut = Future()
            self.qryCandlesAsync(req, callback=partial(set_future_result, fut))
            return fut.result(timeout=timeout) 

    def onQryCandles(self, candles):
        """查询"""
        event1 = Event(type_=EVENT_CANDLES)
        event1.dict_['data'] = candles
        self.eventEngine.put(event1)
        
        # 特定合约代码的事件
        event2 = Event(type_=EVENT_CANDLES + candles.meta.vtSymbol)
        event2.dict_['data'] = candles
        self.eventEngine.put(event2)  

OrigVtGateway = VtGateway
VtGateway = ExtendedGateway
