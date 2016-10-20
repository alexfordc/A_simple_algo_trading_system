# -*- encoding: utf-8 -*-
from BasicClass import *
from Constant import *
from GuiBasic import OrderControlPanel
from collections import OrderedDict
from PyQt4 import QtGui, QtCore


class LimitOrder(object):
    """普通的限价单"""

    def __init__(self, instrument, price, volume, direction, offset, gateway):

        if offset == u'AUTO' or offset == 'AUTO':
            if gateway.position[instrument].get(opposite_direction(direction)) is None:
                offset = OFFSET_OPEN
            else:
                offset = gateway.getOffset(gateway.position[instrument][opposite_direction(direction)], volume)

        req = OrderReq(symbol=instrument, price=price, volume=volume, priceType=PRICETYPE_LIMITPRICE,
            direction=direction, offset=offset)
        gateway.sendOrder(req)


class LimitOrderControlPanel(OrderControlPanel):
    """普通限价单的GUI控制面板"""

    def __init__(self, mainEngine):
        super(LimitOrderControlPanel, self).__init__(mainEngine)

        self.setWindowTitle('Limit Order')

    def _setParaDict(self):
        self._paraDict = OrderedDict()
        self._paraType = {}
        self._paraDict['instrument'] = 'rb1609'
        self._paraDict['price'] = 2500
        self._paraDict['volume'] = 1
        self._paraDict['direction'] = DIRECTION_SHORT
        self._paraDict['offset'] = 'AUTO'
        self._paraDict['gateway'] = 'CTP'

        self._paraType['instrument'] = str
        self._paraType['price'] = float
        self._paraType['volume'] = int
        self._paraType['direction'] = str
        self._paraType['offset'] = unicode
        self._paraType['gateway'] = str
        
    def _initUpperLayout(self):
        self._paraWidget = {}
        for i, paraName in enumerate(self._paraDict.keys()):
            self._upperLayout.addWidget(QtGui.QLabel(paraName), i, 0)
            if paraName == 'direction':
                self._paraWidget[paraName] = QtGui.QComboBox()
                self._paraWidget[paraName].addItems([DIRECTION_LONG, DIRECTION_SHORT])
            elif paraName == 'offset':
                self._paraWidget[paraName] = QtGui.QComboBox()
                self._paraWidget[paraName].addItems(['AUTO', OFFSET_OPEN, OFFSET_CLOSE, OFFSET_CLOSETODAY, OFFSET_CLOSEYESTERDAY])
            else:
                self._paraWidget[paraName] = QtGui.QLineEdit()
                self._paraWidget[paraName].setText(str(self._paraDict[paraName]))
            self._upperLayout.addWidget(self._paraWidget[paraName], i, 1)
    
    def _resetParaValue(self):
        for para, wdgt in self._paraWidget.iteritems():
            if para == 'direction' or para == 'offset':
                self._paraDict[para] = self._paraType[para](wdgt.currentText())
            else:
                self._paraDict[para] = self._paraType[para](wdgt.text())
        self.mainEngine.writeLog('##### RESET LIMIT ORDER PARAMETERS #####') 
        for para, value in self._paraDict.iteritems():
            self.mainEngine.writeLog('{0}: {1}'.format(para, value))

    def _send(self):
        self._resetParaValue()

        self._orderNum += 1
        orderName = '%s.%s.%s' % ('rb1609', self._paraDict['gateway'], self._orderNum)
        self._sentOrderDict[orderName] = LimitOrder(self._paraDict['instrument'], self._paraDict['price'], self._paraDict['volume'], self._paraDict['direction'], 
            self._paraDict['offset'], self.mainEngine.gatewayDict[self._paraDict['gateway']])

    def _cancel(self):
        self.mainEngine.writeLog(u'!!!!!!!! 此版本暂不支持 Regular Limit Order 撤单 !!!!!!!!')

    @property
    def sentOrderStateStr(self):
        return u'!!!!!!!! 此版本暂不支持 Regular Limit Order 查询状态 !!!!!!!!'



def opposite_direction(direction):
    if direction == DIRECTION_LONG:
        return DIRECTION_SHORT
    elif direction == DIRECTION_SHORT:
        return DIRECTION_LONG


def main():
    from MainEngine import MainEngine
    from AdvancedGateway import inited_with_pos_gateway, log_gateway
    import time

    def print_log(log):
        print(u'<%s> |  %s' % (log.logTime, log.logContent))

    me = MainEngine([log_gateway, inited_with_pos_gateway])
    me.logEvent.subscribe(EventHandler(print_log))
    me.connect('CTP')

    a = LimitOrder('rb1609', 2500, 1, DIRECTION_LONG, u'AUTO', me.gatewayDict['CTP'])

if __name__ == '__main__':
    main()