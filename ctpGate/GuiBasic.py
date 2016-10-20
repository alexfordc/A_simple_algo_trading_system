# -*- encoding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from collections import OrderedDict


class OrderControlPanel(QtGui.QWidget):
    """订单控制面板基础类，其他订单控制面板需要继承这个类"""

    def __init__(self, mainEngine):
        super(OrderControlPanel, self).__init__()

        self.mainEngine = mainEngine

        self.setFont(QtGui.QFont('Microsoft Yahei', 10))

        self._upperLayout = QtGui.QGridLayout()
        vbox = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        self._confirmButton = QtGui.QPushButton(u'确认参数')
        self._sendButton = QtGui.QPushButton(u'下  单')
        self._queryButton = QtGui.QPushButton(u'查询状态')
        self._cancelButton = QtGui.QPushButton(u'撤  单')

        hbox1.addWidget(self._sendButton)
        hbox1.addWidget(self._cancelButton)
        hbox2.addWidget(self._confirmButton)
        hbox2.addWidget(self._queryButton)
        vbox.addLayout(self._upperLayout)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox1)

        self.setLayout(vbox)

        self._setParaDict()

        self._sentOrderDict = OrderedDict()

        self._orderNum = 0

        self._initUpperLayout()

        self._qrySentOrderBox = QrySentOrderBox(self)

        self._connectButtons()

    def _setParaDict(self):
        raise NotImplementedError

    def _initUpperLayout(self):
        raise NotImplementedError

    def _resetParaValue(self):
        raise NotImplementedError

    def _send(self):
        raise NotImplementedError

    def _cancel(self):
        raise NotImplementedError

    @property
    def sentOrderStateStr(self):
        raise NotImplementedError

    def _connectButtons(self):
        self._queryButton.clicked.connect(self._qrySentOrderBox.update)
        self._queryButton.clicked.connect(self._qrySentOrderBox.show)
        self._sendButton.clicked.connect(self._send)
        self._confirmButton.clicked.connect(self._resetParaValue)
        self._cancelButton.clicked.connect(self._cancel)


class QrySentOrderBox(QtGui.QWidget):
    """查询订单状态界面"""

    def __init__(self, strategy):
        super(QrySentOrderBox, self).__init__()

        screen = QtGui.QDesktopWidget().screenGeometry()
        windowLocX, windowLocY = screen.width() / 1.5, screen.height() / 5
        windowSizeX, windowSizeY = screen.width() / 4, screen.height() / 3
        self.setGeometry(windowLocX, windowLocY, windowSizeX, windowSizeY)

        vbox = QtGui.QHBoxLayout()
        self.setLayout(vbox)

        textWidget = QtGui.QTextEdit()
        textWidget.setReadOnly(True)
        textWidget.setFont(QtGui.QFont('Microsoft Yahei', 10))

        self._textWidget = textWidget

        vbox.addWidget(textWidget)

        self.setWindowTitle('STRATEGY STATE')

        self.strategy = strategy

    def update(self):
        """更新状态信息"""
        self._textWidget.setText(self.strategy.sentOrderStateStr)


class ChooseBox(QtGui.QDialog):
    """弹出选择框"""
    
    def __init__(self, title, msg, chooseList, obj, varName):
        super(ChooseBox, self).__init__()

        self.obj = obj
        self.varName = varName

        self.setWindowTitle(title)

        vbox = QtGui.QVBoxLayout()

        vbox.addWidget(QtGui.QLabel(msg))

        for choice in chooseList:
            button = QtGui.QPushButton(choice, self)
            vbox.addWidget(button)

            self.connect(button, QtCore.SIGNAL('clicked()'), self.buttonClicked)

        self.setLayout(vbox)

    def buttonClicked(self):
        sender = self.sender()
        self.obj.__setattr__(self.varName, sender.text())
        self.close()

