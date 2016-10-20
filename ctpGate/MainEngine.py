# -*- encoding: utf-8 -*-
from BasicClass import *
from OrderBuffer import OrderBuffer
from CtpGateway import CtpGateway
from Event import Event, EventEngine, EventHandler

import json, time
from collections import OrderedDict


class MainEngine(object):

    def __init__(self, gatewayWrappers=[]):
        self.__initEvent()
        
        self.__gatewayWrappers = gatewayWrappers
        self.__contractDict = {}
        self.__initGateway()

        self.loadContractsInfo()

    def __initEvent(self):

        self.eventEngine = EventEngine()

        # Gateway event
        self.tickDataEvent = Event(self.eventEngine, 'tick')
        self.tradeEvent = Event(self.eventEngine, 'trade')
        self.orderEvent = Event(self.eventEngine, 'order')
        self.positionEvent = Event(self.eventEngine, 'position')
        self.accountEvent = Event(self.eventEngine, 'account')
        self.contractEvent = Event(self.eventEngine, 'contract')
        self.errorEvent = Event(self.eventEngine, 'error')
        self.cancelEvent = Event(self.eventEngine, 'cancel')

        # System Event
        self.timerEvent = Event(self.eventEngine, 'timer')
        self.logEvent = Event(self.eventEngine, 'log')

        # Order Event
        self.insertEvent = Event(self.eventEngine, 'insert')
        self.allTradeEvent = Event(self.eventEngine, 'all_trade')
        self.orderStatusChangeEvent = Event(self.eventEngine, 'order_status_change')

        self.eventEngine.start()

        self.contractEvent.subscribe(EventHandler(self.updateContractsInfo))
    
    def __initGateway(self):

        self.gatewayDict = OrderedDict()

        # try:
        #     self.__createGateway(CtpGateway, 'CTP')
        # except Exception as e:
        #     print e
        self.__createGateway(CtpGateway, 'CTP')

    def __createGateway(self, originGatewayClass, gatewayName=None):
        finalGateway = originGatewayClass
        for func in self.__gatewayWrappers:
            finalGateway = func(finalGateway)
        self.gatewayDict[gatewayName] = finalGateway(self, gatewayName)
        
    def connect(self, gatewayName):
        # try:
        gateway = self.gatewayDict[gatewayName]
        gateway.connect()
        # except Exception as e:
        #     print e

    def subscribe(self, subReq, gatewayName):
        try:
            gateway = self.gatewayDict[gatewayName]
            gateway.subscribe(subReq)
        except Exception as e:
            print e

    def qryContracts(self):
        for gate in self.gatewayDict.itervalues():
            gate.qryInstrument()

    def updateContractsInfo(self, contract):
        self.__contractDict[contract.symbol] = contract.__dict__
    
    def getContractInfo(self, symbol, info):
        """
        Return None if not exists. 
        symbol, info: str
        """
        d = self.__contractDict.get(symbol, {})
        return d.get(info)

    def saveContractsInfo(self):
        f = file('contracts.json', mode='w')
        json.dump(self.__contractDict, f, sort_keys=True, indent=4)
        f.close()
    
    def loadContractsInfo(self):
        f = file('contracts.json')
        self.__contractDict = json.load(f)
        f.close()

    def writeLog(self, text):
        self.logEvent.emit(LogData(text))


def main():
    
    from AdvancedGateway import log_gateway, inited_with_pos_gateway
    import time

    def print_log(log):
        print(u'<%s> |  %s' % (log.logTime, log.logContent))

    me = MainEngine([log_gateway, inited_with_pos_gateway])
    me.logEvent.subscribe(EventHandler(print_log))
    me.connect('CTP')

if __name__ == '__main__':
    main()