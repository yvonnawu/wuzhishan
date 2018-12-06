from vnpy.trader.vtConstant import VN_SEPARATOR

from .manager import BarManager, BarManagerPlugin
from ..ctaPlugin import CtaTemplateWithPlugins, CtaEngineWithPlugins
from ...ctaBacktesting import BacktestingEngine as OriginBacktestingEngine
from ...ctaTemplate import CtaTemplate as OriginCtaTemplate
from ...histbar import BarReader


class CtaEngine(CtaEngineWithPlugins):
    def __init__(self, mainEngine, eventEngine):
        super(CtaEngine, self).__init__(mainEngine, eventEngine)
        self.addPlugin(BarManagerPlugin())
        self._barReaders = {}

    def getBarReader(self, gatewayName):
        if gatewayName not in self._barReaders:
            self._barReaders[gatewayName] = BarReader.new(self.getGateway(gatewayName))
        return self._barReaders[gatewayName]

    def getBarReaderBySymbol(self, symbol):
        _, gatewayName = symbol.split(VN_SEPARATOR)
        return self.getBarReader(gatewayName)

    def getArrayManager(self, symbol, freq="1m"):
        p = self.getPlugin(BarManagerPlugin)
        return p.manager.get_array_manager(symbol, freq=freq)

    def setArrayManagerSize(self, size):
        p = self.getPlugin(BarManagerPlugin)
        return p.manager.set_size(size)

    def loadStrategy(self, setting):
        super(CtaEngine, self).loadStrategy(setting)
        p = self.getPlugin(BarManagerPlugin)
        try:
            name = setting['name']
            strategy = self.strategyDict[name]
        except KeyError as e:
            return
        if isinstance(strategy, CtaTemplate):
            p.manager.register_strategy(strategy)


class CtaTemplate(CtaTemplateWithPlugins):
    def getArrayManager(self, symbol, freq="1m"):
        return self.ctaEngine.getArrayManager(symbol, freq=freq)

    def setArrayManagerSize(self, size):
        return self.ctaEngine.setArrayManagerSize(size)


class BacktestingEngine(OriginBacktestingEngine):
    def __init__(self):
        super(BacktestingEngine, self).__init__()
        self.barManager = None
        self.__prev_bar = None

    def setArrayManagerSize(self, size):
        return self.barManager.set_size(size)

    def getArrayManager(self, symbol, freq="1m"):
        return self.barManager.get_array_manager(symbol, freq=freq)

    def runBacktesting(self):
        if isinstance(self.strategy, CtaTemplate):
            self.barManager = BarManager(self)
            self.barManager.set_mode(self.mode)
            self.barManager.register_strategy(self.strategy)
            self.__prev_bars = None
        super(BacktestingEngine, self).runBacktesting()

    def newBar(self, bar):
        if isinstance(self.strategy, CtaTemplate):
            # NOTE: there is one bar lag behind
            prev_bar = self.__prev_bar
            if prev_bar:
                self.barDict[bar.vtSymbol] = prev_bar
                self.dt = prev_bar.datetime
                self.crossLimitOrder(prev_bar)
                self.crossStopOrder(prev_bar)
            self.barManager.on_bar(bar) # equal to: self.strategy.onBar(prev_bar)
            if prev_bar:
                self.updateDailyClose(prev_bar.vtSymbol, prev_bar.datetime, prev_bar.close)
            self.__prev_bar = bar
        else:
            super(BacktestingEngine, self).newBar(bar)
        
    def newTick(self, tick):
        if isinstance(self.strategy, CtaTemplate):
            self.tickDict[tick.vtSymbol] = tick
            self.dt = tick.datetime
            self.crossLimitOrder(tick)
            self.crossStopOrder(tick)
            self.barManager.on_tick(tick)
            self.strategy.onTick(tick)
            self.updateDailyClose(tick.vtSymbol, tick.datetime, tick.lastPrice)
        else:
            super(BacktestingEngine, self).newTick(tick)
