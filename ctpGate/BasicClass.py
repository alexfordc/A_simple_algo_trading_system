# -*- encoding: utf-8 -*-
from Event import EventHandler
from Constant import *

import datetime


class BasicGateway(object):
    """基础Gateway类，所有Gateway都必须继承这个类"""

    def __init__(self, mainEngine, gatewayName):
        self._inited = False
        self.gatewayName = gatewayName
        self.mainEngine = mainEngine

        self.subscribeEvents()
    
    def subscribeEvents(self):
        
        # 使用默认priority=0
        self.mainEngine.tickDataEvent.subscribe(EventHandler(self._onTick))
        self.mainEngine.tradeEvent.subscribe(EventHandler(self._onTrade))
        self.mainEngine.orderEvent.subscribe(EventHandler(self._onOrder))
        self.mainEngine.positionEvent.subscribe(EventHandler(self._onPosition))
        self.mainEngine.accountEvent.subscribe(EventHandler(self._onAccount))
        self.mainEngine.contractEvent.subscribe(EventHandler(self._onContract))
        self.mainEngine.errorEvent.subscribe(EventHandler(self._onError))
        self.mainEngine.cancelEvent.subscribe(EventHandler(self._onCancel))
    
    def _onTick(self, tick):
        """市场行情推送"""
        pass
    
    def _onTrade(self, trade):
        """成交信息推送"""
        pass
    
    def _onOrder(self, order):
        """订单回报推送"""
        pass
    
    def _onPosition(self, position):
        """持仓信息推送"""
        pass
    
    def _onAccount(self, account):
        """账户信息推送"""
        pass
    
    def _onError(self, error):
        """错误信息推送"""
        pass
    
    def _onContract(self, contract):
        """合约基础信息推送"""
        pass
    
    def _onCancel(self, order):
        """撤单信息推送"""
        pass

    def connect(self):
        """连接"""
        raise NotImplementedError
    
    def subscribe(self, subscribeReq):
        """订阅行情"""
        pass

    def sendOrder(self, orderReq):
        """发单"""
        raise NotImplementedError

    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        raise NotImplementedError

    def qryAccount(self):
        """查询账户资金"""
        pass

    def qryPosition(self):
        """查询持仓"""
        pass

    def getContractInfo(self, symbol, info):
        return self.mainEngine.getContractInfo(symbol, info)


class BasicData(object):

    def setAttribute(self, dataDict):
        """调用__setattr__保存dataDict中的数据, dataDict的key必须为`str`"""
        for key, value in dataDict.iteritems():
            self.__setattr__(key, value)


class TickData(BasicData):
    """Tick行情数据类"""

    def __init__(self):

        # 代码相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        # 成交数据
        self.lastPrice = EMPTY_FLOAT            # 最新成交价
        self.lastVolume = EMPTY_INT             # 最新成交量
        self.volume = EMPTY_INT                 # 今天总成交量
        self.openInterest = EMPTY_INT           # 持仓量
        self.time = EMPTY_STRING                # 时间 11:20:56.5
        self.date = EMPTY_STRING                # 日期 20151009

        # 常规行情
        self.openPrice = EMPTY_FLOAT            # 今日开盘价
        self.highPrice = EMPTY_FLOAT            # 今日最高价
        self.lowPrice = EMPTY_FLOAT             # 今日最低价
        self.preClosePrice = EMPTY_FLOAT

        self.upperLimit = EMPTY_FLOAT           # 涨停价
        self.lowerLimit = EMPTY_FLOAT           # 跌停价

        # 五档行情
        self.bidPrice1 = EMPTY_FLOAT
        self.bidPrice2 = EMPTY_FLOAT
        self.bidPrice3 = EMPTY_FLOAT
        self.bidPrice4 = EMPTY_FLOAT
        self.bidPrice5 = EMPTY_FLOAT

        self.askPrice1 = EMPTY_FLOAT
        self.askPrice2 = EMPTY_FLOAT
        self.askPrice3 = EMPTY_FLOAT
        self.askPrice4 = EMPTY_FLOAT
        self.askPrice5 = EMPTY_FLOAT

        self.bidVolume1 = EMPTY_INT
        self.bidVolume2 = EMPTY_INT
        self.bidVolume3 = EMPTY_INT
        self.bidVolume4 = EMPTY_INT
        self.bidVolume5 = EMPTY_INT

        self.askVolume1 = EMPTY_INT
        self.askVolume2 = EMPTY_INT
        self.askVolume3 = EMPTY_INT
        self.askVolume4 = EMPTY_INT
        self.askVolume5 = EMPTY_INT


class TradeData(BasicData):
    """成交数据类"""

    def __init__(self):

        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        self.tradeID = EMPTY_STRING             # 成交编号
        self.vtTradeID = EMPTY_STRING           # 成交在vt系统中的唯一编号，通常是 Gateway名.成交编号

        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

        # 成交相关
        self.direction = EMPTY_UNICODE          # 成交方向
        self.offset = EMPTY_UNICODE             # 成交开平仓
        self.price = EMPTY_FLOAT                # 成交价格
        self.volume = EMPTY_INT                 # 成交数量
        self.tradeTime = EMPTY_STRING           # 成交时间


class OrderData(BasicData):
    """订单数据类"""

    def __init__(self):

        # 代码编号相关
        self.symbol = EMPTY_STRING              # 合约代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码

        self.orderID = EMPTY_STRING             # 订单编号
        self.vtOrderID = EMPTY_STRING           # 订单在vt系统中的唯一编号，通常是 Gateway名.订单编号

        # 报单相关
        self.direction = EMPTY_UNICODE          # 报单方向
        self.offset = EMPTY_UNICODE             # 报单开平仓
        self.price = EMPTY_FLOAT                # 报单价格
        self.totalVolume = EMPTY_INT            # 报单总数量
        self.tradedVolume = EMPTY_INT           # 报单成交数量
        self.status = EMPTY_UNICODE             # 报单状态

        self.orderTime = EMPTY_STRING           # 发单时间
        self.cancelTime = EMPTY_STRING          # 撤单时间

        # CTP/LTS相关
        self.frontID = EMPTY_INT                # 前置机编号
        self.sessionID = EMPTY_INT              # 连接编号


class PositionData(BasicData):
    """持仓数据类"""

    def __init__(self, symbol=EMPTY_STRING, exchange=EMPTY_STRING, vtSymbol=EMPTY_STRING, direction=EMPTY_STRING, 
            position=EMPTY_INT, tdFrozen=EMPTY_INT, ydFrozen=EMPTY_INT, price=EMPTY_FLOAT, vtPositionName=EMPTY_STRING, ydPosition=EMPTY_INT):

        # 代码编号相关
        self.symbol = symbol                    # 合约代码
        self.exchange = exchange                # 交易所代码
        self.vtSymbol = vtSymbol                # 合约在vt系统中的唯一代码，合约代码.交易所代码

        # 持仓相关
        self.direction = direction              # 持仓方向
        self.position = position                # 持仓量
        self.tdFrozen = tdFrozen                # 仅对于SHFE
        self.ydFrozen = ydFrozen                # 仅对于SHFE
        self.price = price                      # 持仓均价
        self.vtPositionName = vtPositionName    # 持仓在vt系统中的唯一代码，通常是vtSymbol.方向

        self.ydPosition = ydPosition            # 昨持仓

    @property
    def tdPosition(self):
        return self.position - self.ydPosition
    
    @property
    def frozen(self):
        return self.tdFrozen + self.ydFrozen


class AccountData(BasicData):
    """账户数据类"""

    def __init__(self):

        # 账号代码相关
        self.accountID = EMPTY_STRING           # 账户代码
        self.vtAccountID = EMPTY_STRING         # 账户在vt中的唯一代码，通常是 Gateway名.账户代码

        # 数值相关
        self.preBalance = EMPTY_FLOAT           # 昨日账户结算净值
        self.balance = EMPTY_FLOAT              # 账户净值
        self.available = EMPTY_FLOAT            # 可用资金
        self.commission = EMPTY_FLOAT           # 今日手续费
        self.margin = EMPTY_FLOAT               # 保证金占用
        self.closeProfit = EMPTY_FLOAT          # 平仓盈亏
        self.positionProfit = EMPTY_FLOAT       # 持仓盈亏


class ErrorData(BasicData):
    """错误数据类"""

    def __init__(self):

        self.errorID = EMPTY_STRING             # 错误代码
        self.errorMsg = EMPTY_UNICODE           # 错误信息
        self.additionalInfo = EMPTY_UNICODE     # 补充信息


class LogData(BasicData):
    """日志数据类"""

    def __init__(self, logContent=EMPTY_UNICODE):

        self.logTime = '{0}'.format(datetime.datetime.now())          # 日志生成时间
        self.logTime = self.logTime[:23]
        self.logContent = logContent                            # 日志信息


class ContractData(BasicData):
    """合约详细信息类"""

    def __init__(self):

        self.symbol = EMPTY_STRING              # 代码
        self.exchange = EMPTY_STRING            # 交易所代码
        self.vtSymbol = EMPTY_STRING            # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        self.name = EMPTY_UNICODE               # 合约中文名

        self.productClass = EMPTY_UNICODE       # 合约类型
        self.size = EMPTY_INT                   # 合约大小
        self.priceTick = EMPTY_FLOAT            # 合约最小价格TICK

        # 期权相关
        self.strikePrice = EMPTY_FLOAT          # 期权行权价
        self.underlyingSymbol = EMPTY_STRING    # 标的物合约代码
        self.optionType = EMPTY_UNICODE         # 期权类型


class SubscribeReq(BasicData):
    """订阅行情时传入的对象类"""

    def __init__(self, symbol=EMPTY_STRING, exchange=EMPTY_STRING):

        self.symbol = symbol              # 代码
        self.exchange = exchange            # 交易所

        # 以下为IB相关
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.currency = EMPTY_STRING            # 合约货币
        self.expiry = EMPTY_STRING              # 到期日
        self.strikePrice = EMPTY_FLOAT          # 行权价
        self.optionType = EMPTY_UNICODE         # 期权类型


class OrderReq(object):
    """发单时传入的对象类"""

    def __init__(self, symbol=EMPTY_STRING, exchange=EMPTY_STRING, price=EMPTY_FLOAT, volume=EMPTY_INT,
            priceType=EMPTY_STRING, direction=EMPTY_STRING, offset=EMPTY_STRING):

        self.symbol = symbol                    # 代码
        self.exchange = exchange                # 交易所
        self.price = price                      # 价格
        self.volume = volume                    # 数量

        self.priceType = priceType              # 价格类型
        self.direction = direction              # 买卖
        self.offset = offset                    # 开平

        # 以下为IB相关
        self.productClass = EMPTY_UNICODE       # 合约类型
        self.currency = EMPTY_STRING            # 合约货币
        self.expiry = EMPTY_STRING              # 到期日
        self.strikePrice = EMPTY_FLOAT          # 行权价
        self.optionType = EMPTY_UNICODE         # 期权类型


class CancelOrderReq(object):
    """撤单时传入的对象类"""

    def __init__(self, symbol=EMPTY_STRING, exchange=EMPTY_STRING, orderID=EMPTY_STRING,
            frontID=EMPTY_INT, sessionID=EMPTY_INT):

        self.symbol = symbol                # 代码
        self.exchange = exchange            # 交易所

        # 以下字段主要和CTP、LTS类接口相关
        self.orderID = orderID              # 报单号
        self.frontID = frontID              # 前置机号
        self.sessionID = sessionID          # 会话号

