# -*- encoding: utf-8 -*-
from __future__ import division
from PyQt4 import QtGui, QtCore
from collections import OrderedDict
import sys

from MainEngine import MainEngine
from Event import Event, EventHandler
from TwapOrder import TwapOrder, TwapControlPanel
from RegularOrder import LimitOrder, LimitOrderControlPanel
from ExcelOrder import ExcelOrder, ExcelOrderControlPanel
from Constant import *
from AdvancedGateway import inited_with_pos_gateway, log_gateway


class MainWindow(QtGui.QMainWindow):
    """主窗口"""

    def __init__(self):
        super(MainWindow, self).__init__()

        self._mainEngine = MainEngine([inited_with_pos_gateway, log_gateway])

        self.__initUI()

        self._mainEngine.logEvent.subscribe(self.logWidget.onLogEvent)

        self.connectCTP()       # 打开时连接CTP

    def __initUI(self):
        """初始化UI"""
        # 根据屏幕大小，设定窗口大小
        screen = QtGui.QDesktopWidget().screenGeometry()
        windowLocX, windowLocY = screen.width() / 6, screen.height() / 5.5
        windowSizeX, windowSizeY = screen.width() / 1.9, screen.height() / 2.2
        self.setGeometry(windowLocX, windowLocY, windowSizeX, windowSizeY)

        self.setWindowTitle('Main')

        # TWAP ORDER
        self.twapWidget = TwapControlPanel(self._mainEngine)
        twapAction = QtGui.QAction('TWAP Order', self)
        self.connect(twapAction, QtCore.SIGNAL('triggered()'), self.twapWidget.show)

        # Connect CTP
        connectCtpAction = QtGui.QAction(u'连接CTP', self)
        self.connect(connectCtpAction, QtCore.SIGNAL('triggered()'), self.connectCTP)

        # 读取合约信息
        loadContractsAction = QtGui.QAction(u'读取合约信息', self)
        self.connect(loadContractsAction, QtCore.SIGNAL('triggered()'), self.__loadContractsInfo)

        # 更新合约信息
        updateContractsAction = QtGui.QAction(u'更新合约信息', self)
        self.connect(updateContractsAction, QtCore.SIGNAL('triggered()'), self.__updateContractsInfo)

        # 储存合约信息
        saveContractsAction = QtGui.QAction(u'储存合约信息', self)
        self.connect(saveContractsAction, QtCore.SIGNAL('triggered()'), self.__saveContractsInfo)

        # 清空LOG信息
        clearLogAction = QtGui.QAction(u'清空LOG信息', self)
        self.connect(clearLogAction,  QtCore.SIGNAL('triggered()'), self.__clearLog)

        # Limit Order
        self.limitOrderWidget = LimitOrderControlPanel(self._mainEngine)
        limitOrderAction = QtGui.QAction(u'Limit Order', self)
        self.connect(limitOrderAction,  QtCore.SIGNAL('triggered()'), self.limitOrderWidget.show)

        # Excel Order
        self.excelOrderWidget = ExcelOrderControlPanel(self._mainEngine)
        excelOrderAction = QtGui.QAction(u'Excel Order', self)
        self.connect(excelOrderAction,  QtCore.SIGNAL('triggered()'), self.excelOrderWidget.show)

        # Menu Bar
        menubar = self.menuBar()
        systemMenu = menubar.addMenu(u'&系统')
        systemMenu.addAction(connectCtpAction)
        systemMenu.addSeparator()
        systemMenu.addAction(loadContractsAction)
        systemMenu.addAction(updateContractsAction)
        systemMenu.addAction(saveContractsAction)
        systemMenu.addSeparator()
        systemMenu.addAction(clearLogAction)

        # Order Bar
        OrderMenu = menubar.addMenu(u'&下单')
        OrderMenu.addAction(limitOrderAction)
        OrderMenu.addSeparator()
        OrderMenu.addAction(twapAction)
        OrderMenu.addAction(excelOrderAction)

        # Add Log Widget
        self.logWidget = LogWidget()
        self.setCentralWidget(self.logWidget)

    def connectCTP(self):
        self._mainEngine.connect('CTP')

    def closeEvent(self, event):
        """退出时调用此函数"""
        reply = QtGui.QMessageBox.question(self, 'Message', 'Are u sure to quit?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self._mainEngine.eventEngine.stop()
            event.accept()
        else:
            event.ignore()

    def __loadContractsInfo(self):
        self._mainEngine.loadContractsInfo()

    def __updateContractsInfo(self):
        self._mainEngine.qryContracts()

    def __saveContractsInfo(self):
        self._mainEngine.saveContractsInfo()
    
    def __clearLog(self):
        self.logWidget._textWidget.clear()


class LogWidget(QtGui.QWidget):
    """显示LOG的插件"""

    _updateLogSingal = QtCore.pyqtSignal('PyQt_PyObject', name='UpdateLogSignal')

    def __init__(self):
        super(LogWidget, self).__init__()

        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)

        textWidget = QtGui.QTextEdit()
        textWidget.setReadOnly(True)
        textWidget.setFont(QtGui.QFont('Microsoft Yahei', 10))
        textWidget.document().setMaximumBlockCount(5000)

        self._textWidget = textWidget

        hbox.addWidget(textWidget)

        self.connect(self, QtCore.SIGNAL('UpdateLogSignal(PyQt_PyObject)'), self.appendText)

    @QtCore.pyqtSlot('PyQt_PyObject')
    def appendText(self, text):
        self._textWidget.append(text)

    def onLogEvent(self, log):
        logText = u'<%s> |  %s' % (log.logTime, log.logContent)
        self._updateLogSingal.emit(logText)
        # TEST
        # print logText



def test():
    app = QtGui.QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test()

