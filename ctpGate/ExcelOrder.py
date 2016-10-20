# -*- encoding: utf-8 -*-
from BasicClass import *
from Constant import *
from GuiBasic import OrderControlPanel
from ComplexOrder import ComplexOrder
from RegularOrder import LimitOrder

from collections import OrderedDict
from PyQt4 import QtGui, QtCore
import xlwings as xw
import os 


class ExcelOrder(ComplexOrder):
    """暂不需要使用这个类"""

    def __init__(self, gateway, excelPath, excelArea):
        super(ExcelOrder, self).__init__(gateway, None)

        self.excelPath = excelPath
        self.excelArea = excelArea

        self.setParaType()

        self.readExcel()

        self.send()

    def readExcel(self):
        self.wb = xw.Workbook(self.excelPath)
        self.sheet = xw.Sheet('PythonOrder')
        self.range = xw.Range(self.excelArea)

        self.__orderList = [OrderedDict()]
        self.__tempParaList = []
        
        for row in self.range.value:
            paraName, paraValue = row[0], row[1]
            if paraName is not None:
                if paraName in self.__tempParaList:
                    self.__tempParaList = []
                    self.__orderList.append(OrderedDict())
                self.__tempParaList.append(paraName)
                self.__orderList[-1][str(paraName)] = self._paraType[str(paraName)](paraValue)
        
    def send(self):
        for orderInfo in self.__orderList:
            LimitOrder(orderInfo['instrument'], orderInfo['price'], orderInfo['volume'], orderInfo['direction'], orderInfo['offset'], self._gateway)
    
    def setParaType(self):
        self._paraType = {}
        self._paraType['instrument'] = str
        self._paraType['price'] = float
        self._paraType['volume'] = int
        self._paraType['direction'] = str
        self._paraType['offset'] = unicode
        

class ExcelOrderControlPanel(OrderControlPanel):

    def __init__(self, mainEngine):
        super(ExcelOrderControlPanel, self).__init__(mainEngine)

        self.setWindowTitle('Excel Order')
    
    def _setParaDict(self):
        """设定参数类型"""
        self._paraType = {}
        self._paraType['instrument'] = str
        self._paraType['price'] = float
        self._paraType['volume'] = int
        self._paraType['direction'] = str
        self._paraType['offset'] = unicode

    def _initUpperLayout(self):
        msgStr = u'读取最近一次被激活的\nExcel窗口的被选中的单元格.'
        self._upperLayout.addWidget(QtGui.QLabel(msgStr), 0, 0)

    def _resetParaValue(self):
        try:
            self.wb = xw.Workbook.active()
            
            self.__orderList = [OrderedDict()]      # 待发送订单参数列表，每个订单使用一个字典保存参数
            tempParaList = []

            for row in self.wb.get_selection().value:
                paraName, paraValue = row[0], row[1]
                if paraName is not None:
                    if paraName in tempParaList:
                        tempParaList = []
                        self.__orderList.append(OrderedDict())
                    tempParaList.append(paraName)
                    self.__orderList[-1][str(paraName)] = self._paraType[str(paraName)](paraValue)
            
            self.mainEngine.writeLog('##### RESET EXCEL ORDER PARAMETERS #####')
            for i, orderInfo in enumerate(self.__orderList):
                self.mainEngine.writeLog('$$$ ORDER {} $$$'.format(i+1))
                for name, value in orderInfo.iteritems():
                    self.mainEngine.writeLog('{0}: {1}'.format(name, value))
        except Exception as e:
            self.__orderList = []
            self.mainEngine.writeLog(u'!!!!!!!! 读取EXCEL参数时出错 !!!!!!!!')
            self.mainEngine.writeLog(u'!!!!!!!! 请确认单元格是否选择正确 !!!!!!!!')
            self.mainEngine.writeLog(u'%s' % e)
            self.mainEngine.writeLog(u'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def _send(self):
        self._resetParaValue()

        try:
            for orderInfo in self.__orderList:
                LimitOrder(orderInfo['instrument'], orderInfo['price'], orderInfo['volume'], orderInfo['direction'], orderInfo['offset'], self.mainEngine.gatewayDict['CTP'])
        except Exception as e:
            self.mainEngine.writeLog(u'!!!!!!!! 发送EXCEL ORDER时出错 !!!!!!!!')
            self.mainEngine.writeLog(u'%s' % e)
            self.mainEngine.writeLog(u'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def _cancel(self):
        self.mainEngine.writeLog(u'!!!!!!!! 此版本暂不支持 Excel Order 撤单 !!!!!!!!')

    @property
    def sentOrderStateStr(self):
        return u'!!!!!!!! 此版本暂不支持 Excel Order 查询状态 !!!!!!!!'


def test():

    from MainEngine import MainEngine
    from AdvancedGateway import inited_with_pos_gateway, log_gateway
    import time

    def print_log(log):
        print(u'<%s> |  %s' % (log.logTime, log.logContent))

    me = MainEngine([log_gateway, inited_with_pos_gateway])
    me.logEvent.subscribe(EventHandler(print_log))
    me.connect('CTP')

    time.sleep(2)
    ExcelOrder(me.gatewayDict['CTP'], 'D:\\Documents\\Python Scripts\\TEST\\a.xlsx', 'A1:B17')


if __name__ == '__main__':
    test()