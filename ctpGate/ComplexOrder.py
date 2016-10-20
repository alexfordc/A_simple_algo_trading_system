# -*- coding: utf-8 -*-
from Constant import *
from BasicClass import *
from collections import deque
from Event import EventHandler


class ComplexOrder(object):
    """下单算法基础类，各个下单算法必须继承这个类"""

    def __init__(self, gateway, instrument=None):
        self._gateway = gateway
        self._activeOrder = deque()         # 记录生效状态的order
        self._sentOrder = {}                # 记录已发送的order
        self.mdData = {}                    # 记录行情
        
        # 若gateway为连接，则先连接
        if not gateway.mdConnected or not gateway.tdConnected:
            self._printLog(u'%s未连接，正在连接%s...' % (gateway.gatewayName, gateway.gatewayName))
            gateway.connect()
        
        # 建立合约列表
        if instrument is not None:
            if isinstance(instrument, list):
                self.instrList = instrument
                for instr in instrument:
                    subReq = SubscribeReq()
                    subReq.symbol = instr
                    gateway.subscribe(subReq)
            else:
                self.instrList = [instrument]
                subReq = SubscribeReq()
                subReq.symbol = instrument
                gateway.subscribe(subReq)
        
        # 将算法与Gateway连接
        self.__attachToGateway()
    
    @property
    def gateway(self):
        return self._gateway
    
    def onTick(self, tick):
        """收到Tick行情数据时回调"""
        if tick.symbol in self.instrList:
            self.mdData[tick.symbol] = tick
            self._onTick(tick)

    def onTrade(self, trade):
        """收到成交回报时回调"""
        if trade.vtOrderID in self._sentOrder:
            self._onTrade(trade)

    def onOrder(self, order):
        """收到订单回报时回调"""
        if order.vtOrderID in self._activeOrder:
            self._onOrder(order)
    
    def onPosition(self, position):
        """收到持仓回报时回调"""
        if position.symbol in self.instrList:
            self._onPosition(position)
    
    def onAccount(self, account):
        """收到账户回报时回调"""
        pass
    
    def _onTick(self, tick):
        """仅在数据与本order有关时回调"""
        pass
    
    def _onTrade(self, trade):
        """仅在数据与本order有关时回调"""
        pass
    
    def _onOrder(self, order):
        """仅在数据与本order有关时回调"""
        # 若状态为未知，可判定是新发送的order
        if order.status == STATUS_UNKNOWN:
            self._sentOrder[order.vtOrderID] = order
        # 状态为cancel，触发cancel回调，并移出_activeOrder
        elif order.status == STATUS_CANCELLED:
            self._onCancel(order)
            self._activeOrder.remove(order.vtOrderID)
        # All Trade，移出_activeOrder
        elif order.status == STATUS_ALLTRADED:
            self._activeOrder.remove(order.vtOrderID)
    
    def _onCancel(self, order):
        """仅在数据与本order有关时回调"""
        pass
    
    def _onPosition(self, position):
        """仅在数据与本order有关时回调"""
        pass
    
    def sendOrder(self, order):
        """发送订单，并将vtOrderID加入_activeOrder队列"""
        self._activeOrder.append(self._gateway.sendOrder(order))
    
    def cancelOrder(self, req):
        """撤单"""
        self._gateway.cancelOrder(req)
    
    def __attachToGateway(self):
        self._gateway.mainEngine.tickDataEvent.subscribe(EventHandler(self.onTick, priority=10))
        self._gateway.mainEngine.orderEvent.subscribe(EventHandler(self.onOrder, priority=10))
        self._gateway.mainEngine.tradeEvent.subscribe(EventHandler(self.onTrade, priority=10))
        self._gateway.mainEngine.positionEvent.subscribe(EventHandler(self.onPosition, priority=10))
        self._gateway.mainEngine.accountEvent.subscribe(EventHandler(self.onAccount, priority=10))
        # self._gateway.mainEngine.logEvent.subscribe(EventHandler(self.onLog, priority=10))

    def _printLog(self, text):
        log = LogData('%s' % text)
        self._gateway.mainEngine.logEvent.emit(log)


def test():
    from MainEngine import MainEngine
    from AdvancedGateway import inited_with_pos_gateway, log_gateway
    import time

    def print_log(log):
        print(u'<%s> |  %s' % (log.logTime, log.logContent))

    me = MainEngine([log_gateway, inited_with_pos_gateway])
    me.logEvent.subscribe(EventHandler(print_log))
    me.connect('CTP')


    a = ComplexOrder(me.gatewayDict['CTP'], 'ag1612')

    time.sleep(10)


if __name__ == '__main__':
    test()