# encoding: UTF-8

# 修改编码
from __future__ import print_function


# 创建主引擎代理对象
from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import (EVENT_TICK, EVENT_ORDER, EVENT_TRADE,
                                 EVENT_ACCOUNT, EVENT_POSITION, EVENT_LOG,
                                 EVENT_ERROR, EVENT_CONTRACT)
from vnpy.trader.vtObject import VtSubscribeReq, VtOrderReq, VtCancelOrderReq
from vnpy.trader.app.rpcService.rsClient import MainEngineProxy
from vnpy.trader.app.ctaStrategy.ctaBase import EVENT_CTA_LOG, EVENT_CTA_STRATEGY

reqAddress = 'tcp://localhost:6688'
subAddress = 'tcp://localhost:8866'    

ee = EventEngine2()
me = MainEngineProxy(ee)
me.init(reqAddress, subAddress)

#----------------------------------------------------------------------
def printLog(event):
    """打印日志"""
    log = event.dict_['data']
    print(log.logTime, log.logContent)
    
ee.register(EVENT_LOG, printLog)
    

# 载入Web密码
import json
import base64
import datetime

TODAY = str(datetime.datetime.now().date())

with open("WEB_setting.json") as f:
    setting = json.load(f)
    USERNAME = setting['username']
    PASSWORD = setting['password']
    TOKEN = base64.encodestring((TODAY+PASSWORD).encode()).decode().replace('\n','')


# 创建aiohttp对象
from aiohttp import web
import aiohttp_jinja2
import jinja2
import socketio
from queue import Queue


q = Queue()

sio = socketio.AsyncServer()
app = web.Application(debug=False)
routes = web.RouteTableDef()
sio.attach(app)


async def Token(request):
    username = request.query['username']
    password = request.query['password']

    if username == USERNAME and password == PASSWORD:
        return web.json_response({'result_code': 'success', 'data': TOKEN})
    else:
        return web.json_response({'result_code': 'error', 'message': 'wrong username or password'})


async def Gateway(request):
    if request.method == "GET":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        l = me.getAllGatewayDetails()
        return web.json_response({'result_code': 'success', 'data': l})

    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        gatewayName = data.get('gatewayName',None)
        me.connect(gatewayName)
        return web.json_response({'result_code': 'success', 'data': ''})


async def Order(request):
    if request.method == "GET":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})
        data = me.getAllOrders()
        l = [o.__dict__ for o in data]
        return web.json_response({'result_code': 'success', 'data': l})

    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        vtSymbol = data['vtSymbol']
        price = data['price']
        volume = data['volume']
        priceType = data['priceType']
        direction = data['direction']
        offset = data['offset']
        contract = me.getContract(vtSymbol)
        if not contract:
            return web.json_response({'result_code':'error','message':'contract error'})

        priceType_map = {'PRICETYPE_LIMITPRICE': u'限价', 'PRICETYPE_MARKETPRICE': u'市价', 'PRICETYPE_FAK': u'FAK',
                         'PRICETYPE_FOK': u'FOK'}
        direction_map = {'DIRECTION_LONG': u'多', 'DIRECTION_SHORT': u'空'}
        offset_map = {'OFFSET_OPEN': u'开仓', 'OFFSET_CLOSE': u'平仓', 'OFFSET_CLOSETODAY': u'平今',
                      'OFFSET_CLOSEYESTERDAY': u'平昨'}

        req = VtOrderReq()
        req.symbol = contract.symbol
        req.exchange = contract.exchange
        req.price = float(price)
        req.volume = int(volume)
        req.priceType = priceType_map[priceType]
        req.direction = direction_map[direction]
        req.offset = offset_map[offset]
        vtOrderID = me.sendOrder(req, contract.gatewayName)
        return web.json_response({'result_code': 'success', 'data': vtOrderID})

    if request.method == "DELETE":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        vtOrderID = request.query['vtOrderID']
        # 撤单某一委托
        if vtOrderID:
            order = me.getOrder(vtOrderID)
            if not order:
                return web.json_response({'result_code': 'error', 'message': 'vtOrderID error'})

            cancel(order)
        # 全撤
        else:
            l = me.getAllWorkingOrders()
            for order in l:
                cancel(order)
        return web.json_response({'result_code': 'success', 'data': ""})


def cancel(order):
    """撤单"""
    req = VtCancelOrderReq()
    req.orderID = order.orderID
    req.exchange = order.exchange
    req.symbol = order.symbol
    req.frontID = order.frontID
    req.sessionID = order.sessionID
    me.cancelOrder(req, order.gatewayName)


async def Contract(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getAllContracts()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Account(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getAllAccounts()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Position(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getAllPositions()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Log(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getLog()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Error(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getError()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Trade(request):
    token = request.query['token']
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})
    data = me.getAllTrades()
    l = [o.__dict__ for o in data]
    return web.json_response({'result_code': 'success', 'data': l})


async def Tick(request):
    data = request.content
    data = json.loads(data._buffer[0])
    token = data.get('token', None)
    if token != TOKEN:
        return web.json_response({'result_code': 'error', 'message': 'token error'})

    vtSymbol = data.get('vtSymbol', None)

    contract = me.getContract(vtSymbol)
    if not contract:
        return web.json_response({'result_code': 'error', 'message': 'contract error'})

    req = VtSubscribeReq()
    req.symbol = contract.symbol
    req.exchange = contract.exchange
    req.vtSymbol = contract.vtSymbol

    me.subscribe(req, contract.gatewayName)
    return web.json_response({'result_code': 'success', 'data': ''})


async def CtaStrategyLoad(request):
    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        engine = me.getApp('CtaStrategy')
        engine.loadSetting()
        l = engine.getStrategyNames()
        return web.json_response({'result_code': 'success', 'data': l})


async def CtaStrategyInit(request):
    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = data['name']

        engine = me.getApp('CtaStrategy')
        if not name:
            engine.initAll()
        else:
            engine.initStrategy(name)
        return web.json_response({'result_code': 'success', 'data': ''})


async def CtaStrategyStart(request):
    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = data['name']

        engine = me.getApp('CtaStrategy')
        if not name:
            engine.startAll()
        else:
            engine.startStrategy(name)
        return web.json_response({'result_code': 'success', 'data': ''})


async def CtaStrategyStop(request):
    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = data['name']

        engine = me.getApp('CtaStrategy')
        if not name:
            engine.stopAll()
        else:
            engine.stopStrategy(name)
        return web.json_response({'result_code': 'success', 'data': ''})


async def CtaStrategyRestore(request):
    if request.method == "POST":
        data = request.content
        data = json.loads(data._buffer[0])
        token = data.get('token', None)
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = data['name']

        engine = me.getApp('CtaStrategy')
        engine.restoreStrategy(name)
        return web.json_response({'result_code': 'success', 'data': ''})


async def CtaStrategyParam(request):
    if request.method == "GET":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = request.query['name']

        engine = me.getApp('CtaStrategy')
        l = engine.getStrategyParam(name)
        return web.json_response({'result_code': 'success', 'data': l})


async def CtaStrategyVar(request):
    if request.method == "GET":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        name = request.query['name']

        engine = me.getApp('CtaStrategy')
        l = engine.getStrategyVar(name)
        return web.json_response({'result_code': 'success', 'data': l})


async def CtaStrategyName(request):
    if request.method == "GET":
        token = request.query['token']
        if token != TOKEN:
            return web.json_response({'result_code': 'error', 'message': 'token error'})

        engine = me.getApp('CtaStrategy')
        l = engine.getStrategyNames()
        return web.json_response({'result_code': 'success', 'data': l})


@aiohttp_jinja2.template('index.html')
async def Index(request):
    with open('./templates/index.html',encoding='utf-8') as f:
        return web.Response(text=f.read(), content_type='text/html')


app.router.add_get('/', Index)
app.router.add_get('/token', Token)
app.router.add_get('/gateway', Gateway)
app.router.add_post('/gateway', Gateway)
app.router.add_get('/contract', Contract)
app.router.add_get('/account', Account)
app.router.add_get('/position', Position)
app.router.add_get('/log', Log)
app.router.add_get('/error', Error)
app.router.add_post('/tick', Tick)
app.router.add_get('/trades', Trade)
app.router.add_get('/order', Order)
app.router.add_post('/order', Order)
app.router.add_delete('/order', Order)
app.router.add_static('/static/', path=str('./static'), name='static')

app.router.add_post('/ctastrategy/load', CtaStrategyLoad)
app.router.add_post('/ctastrategy/init', CtaStrategyInit)
app.router.add_post('/ctastrategy/start', CtaStrategyStart)
app.router.add_post('/ctastrategy/stop', CtaStrategyStop)
app.router.add_post('/ctastrategy/restore', CtaStrategyRestore)
app.router.add_get('/ctastrategy/param', CtaStrategyParam)
app.router.add_get('/ctastrategy/var', CtaStrategyVar)
app.router.add_get('/ctastrategy/name', CtaStrategyName)


# 处理事件
def handleEvent(event):
    """处理事件"""
    q.put(event)


ee.register(EVENT_TICK, handleEvent)
ee.register(EVENT_ORDER, handleEvent)
ee.register(EVENT_TRADE, handleEvent)
ee.register(EVENT_ACCOUNT, handleEvent)
ee.register(EVENT_POSITION, handleEvent)
ee.register(EVENT_CONTRACT, handleEvent)
ee.register(EVENT_LOG, handleEvent)
ee.register(EVENT_ERROR, handleEvent)
ee.register(EVENT_CTA_LOG, handleEvent)
ee.register(EVENT_CTA_STRATEGY, handleEvent)


async def background_task():
    """Example of how to send server generated events to clients."""
    while True:
        if not q.empty():
            event = q.get()
            eventType = event.type_
            eventData = event.dict_['data']
            if not isinstance(eventData, dict):
                eventData = eventData.__dict__
            if eventType == 'eTick.':
                # print(eventData)
                del eventData['datetime']
            await sio.emit(eventType, eventData)
        await sio.sleep(0.01)


# ----------------------------------------------------------------------
def run():
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))
    sio.start_background_task(background_task)
    web.run_app(app)


if __name__ == '__main__':
    run()
