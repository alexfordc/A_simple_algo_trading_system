# -*- encoding: utf-8 -*-
import time

from OrderBuffer import OrderBuffer
from BasicClass import *


def log_gateway(gatewayClass):
    """返回一个能够推送信息的Gateway"""

    class LogGateway(gatewayClass):

        def _onTick(self, tick):
            super(LogGateway, self)._onTick(tick)

            self.mainEngine.logEvent.emit(LogData(u'[%s] Market Data: [%s]   [Ask] %s - %s  [Bid] %s - %s  [Trade] %s - %s' % (tick.time,
                tick.symbol, tick.askPrice1, tick.askVolume1, tick.bidPrice1, tick.bidVolume1, tick.lastPrice, tick.lastVolume)))

        def _onTrade(self, trade):
            super(LogGateway, self)._onTrade(trade)

            self.mainEngine.logEvent.emit(LogData(u'[%s] Order [%s] on Trade: [%s]   Price: [%s]  Volume: [%s]  Direction: [%s]  Offset: [%s]' % (
                trade.tradeTime, trade.orderID, trade.symbol, trade.price, trade.volume, trade.direction, trade.offset)))
        
        def _onOrder(self, order):
            super(LogGateway, self)._onOrder(order)

            self.mainEngine.logEvent.emit(LogData(u'Return Order [%s]: [%s]   Price: [%s]  Volume: [%s]  Traded: [%s]  Direction: [%s]  Offset: [%s]  Status: [%s]' % (
                order.orderID, order.symbol, order.price, order.totalVolume, order.tradedVolume, order.direction, order.offset, order.status)))
        
        def _onCancel(self, order):
            super(LogGateway, self)._onCancel(order)

            self.mainEngine.logEvent.emit(LogData(u'Order [%s] on Cancel: [%s]   Price: [%s]  Volume: [%s]  Traded: [%s]  Direction: [%s]  Offset: [%s]' % (
                order.orderID, order.symbol, order.price, order.totalVolume, order.tradedVolume, order.direction, order.offset)))
        
        def _onPosition(self, position):
            super(LogGateway, self)._onPosition(position)

            self.mainEngine.logEvent.emit(LogData(u'Position Info: [%s]   Position: [%s] (td: [%s] yd: [%s])   Direction: [*%s*]   Frozen: [%s] (td: [%s] yd: [%s])' % (
                position.symbol, position.position, position.tdPosition, position.ydPosition, position.direction, position.frozen, position.tdFrozen, position.ydFrozen)))
        
        def _onError(self, error):
            super(LogGateway, self)._onError(error)

            self.mainEngine.logEvent.emit(LogData(u'ERROR: ID: [%s]  Msg: [%s]  Additional: [%s]' % (error.errorID, error.errorMsg, error.additionalInfo)))
        
    return LogGateway


def inited_with_pos_gateway(gatewayClass):
    """返回一个初始化持仓的Gateway"""

    class InitedPosGateway(gatewayClass):

        def connect(self):
            super(InitedPosGateway, self).connect()

            time.sleep(5)

            for _ in xrange(10):
                if len(self.position) == 0:
                    self.qryPosition()
                    time.sleep(0.1)
                else:
                    self._inited = True
                    break
            else:
                self.mainEngine.logEvent.emit(LogData(u'获取持仓信息失败，请重新连接CTP'))
    
    return InitedPosGateway