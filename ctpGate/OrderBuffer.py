# -*- encoding: utf-8 -*-
from Event import EventHandler
from Constant import *
from BasicClass import *


class OrderBuffer(object):
    """订单缓存，用于记录冻结仓位，判断开平仓。暂未实现自成交处理"""

    def __init__(self, mainEngine, gateway):
        self.gateway = gateway
        self.mainEngine = mainEngine
        self.__orderDict = {}               # 保存已发送的order

        self.__subscribeEvents()
    
    def __onOrderInsert(self, order):
        self.__orderDict[order.vtOrderID] = order.__dict__.copy()       # 已发送的order保存为该订单状态字典的拷贝（因为要判断状态变化）

        if self.gateway._inited:

            # 初始化持仓
            if self.gateway.position.get(order.symbol, None) is None:
                self.gateway.position[order.symbol] = {}
                self.gateway.position[order.symbol][DIRECTION_LONG] = PositionData(symbol=order.symbol, direction=DIRECTION_LONG)
                self.gateway.position[order.symbol][DIRECTION_SHORT] = PositionData(symbol=order.symbol, direction=DIRECTION_SHORT)
            
            # 上期所发出平今，返回未知
            if order.offset == OFFSET_UNKNOWN:
                self.gateway.position[order.symbol][opposite_direction(order.direction)].tdFrozen += order.totalVolume
            # 返回平仓，不区分上期所。因为非上期所只有昨冻结仓
            elif order.offset == OFFSET_CLOSE:
                self.gateway.position[order.symbol][opposite_direction(order.direction)].ydFrozen += order.totalVolume

            position = self.gateway.position[order.symbol][opposite_direction(order.direction)]
            self.mainEngine.logEvent.emit(LogData(u'Position Updated on Insert! [%s]   Position: [%s] (yd: [%s])   Direction: [%s]   Frozen: [%s] (td: [%s])' % (
                position.symbol, position.position, position.ydPosition, position.direction, position.frozen, position.tdFrozen)))

    def __onOrderCancel(self, order):
        del self.__orderDict[order.vtOrderID]

        if self.gateway._inited:
            cancelNum = order.totalVolume - order.tradedVolume
            # 上期所发出平今，返回未知
            if order.offset == OFFSET_UNKNOWN:
                self.gateway.position[order.symbol][opposite_direction(order.direction)].tdFrozen -= cancelNum
            # 返回平仓，不区分上期所。因为非上期所只有昨冻结仓
            elif order.offset == OFFSET_CLOSE:
                self.gateway.position[order.symbol][opposite_direction(order.direction)].ydFrozen -= cancelNum

            position = self.gateway.position[order.symbol][opposite_direction(order.direction)]
            self.mainEngine.logEvent.emit(LogData(u'Position Updated on Cancel! [%s]   Position: [%s] (yd: [%s])   Direction: [%s]   Frozen: [%s] (td: [%s])' % (
                position.symbol, position.position,  position.ydPosition, position.direction, position.frozen, position.tdFrozen)))
    
    def __onOrderAllTrade(self, order):
        del self.__orderDict[order.vtOrderID]
   
    def __onOrderStatusChange(self, order):
        if order.status == STATUS_ALLTRADED:
            self.__onOrderAllTrade(order)
        elif order.status == STATUS_CANCELLED:
            self.__onOrderCancel(order)
    
    def __onOrder(self, order):
        if order.vtOrderID not in self.__orderDict:
            self.__onOrderInsert(order)
        else:
            lastStatus = self.__orderDict[order.vtOrderID]['status']
            nowStatus = order.status
            if nowStatus != lastStatus:
                self.__onOrderStatusChange(order)

    def __onTrade(self, trade):

        if self.gateway._inited:
            # 上期所平今
            if trade.offset == OFFSET_CLOSETODAY:
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].tdFrozen -= trade.volume
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].position -= trade.volume
            # 上期所平昨
            elif trade.offset == OFFSET_CLOSEYESTERDAY:
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].ydFrozen -= trade.volume
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].ydPosition -= trade.volume
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].position -= trade.volume
            # 非上期所平仓
            elif trade.offset == OFFSET_CLOSE:
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].ydFrozen -= trade.volume
                self.gateway.position[trade.symbol][opposite_direction(trade.direction)].position -= trade.volume
            # 开仓
            elif trade.offset == OFFSET_OPEN:
                self.gateway.position[trade.symbol][trade.direction].position += trade.volume

            position = self.gateway.position[trade.symbol][opposite_direction(trade.direction)]
            self.mainEngine.logEvent.emit(LogData(u'Position Updated on Trade! [%s]  Position: [%s] (yd: [%s])  Direction: [*%s*]  Frozen: [%s] (td: [%s])' % (
                position.symbol, position.position, position.ydPosition, position.direction, position.frozen, position.tdFrozen)))
            position = self.gateway.position[trade.symbol][trade.direction]
            self.mainEngine.logEvent.emit(LogData(u'Position Updated on Trade! [%s]  Position: [%s] (yd: [%s])  Direction: [*%s*]  Frozen: [%s] (td: [%s])' % (
                position.symbol, position.position, position.ydPosition, position.direction, position.frozen, position.tdFrozen)))

    def __subscribeEvents(self):
        # 需要在其他逻辑之前处理，优先级最高
        self.mainEngine.orderEvent.subscribe(EventHandler(self.__onOrder, priority=-10))
        self.mainEngine.tradeEvent.subscribe(EventHandler(self.__onTrade, priority=-10))


def opposite_direction(direction):
    if direction == DIRECTION_LONG:
        return DIRECTION_SHORT
    elif direction == DIRECTION_SHORT:
        return DIRECTION_LONG
