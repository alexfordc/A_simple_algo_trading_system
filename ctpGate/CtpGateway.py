# -*- encoding: utf-8 -*-

import os
import json
from copy import copy

from vnctpmd import MdApi
from vnctptd import TdApi
from ctpDataType import *
from BasicClass import *
from Constant import *
from OrderBuffer import OrderBuffer


# 以下为一些VT类型和CTP类型的映射字典
# 价格类型映射
priceTypeMap = {}
priceTypeMap[PRICETYPE_LIMITPRICE] = defineDict["THOST_FTDC_OPT_LimitPrice"]
priceTypeMap[PRICETYPE_MARKETPRICE] = defineDict["THOST_FTDC_OPT_AnyPrice"]
priceTypeMapReverse = {v: k for k, v in priceTypeMap.items()}

# 方向类型映射
directionMap = {}
directionMap[DIRECTION_LONG] = defineDict['THOST_FTDC_D_Buy']
directionMap[DIRECTION_SHORT] = defineDict['THOST_FTDC_D_Sell']
directionMapReverse = {v: k for k, v in directionMap.items()}

# 开平类型映射
offsetMap = {}
offsetMap[OFFSET_OPEN] = defineDict['THOST_FTDC_OF_Open']
offsetMap[OFFSET_CLOSE] = defineDict['THOST_FTDC_OF_Close']
offsetMap[OFFSET_CLOSETODAY] = defineDict['THOST_FTDC_OF_CloseToday']
offsetMap[OFFSET_CLOSEYESTERDAY] = defineDict['THOST_FTDC_OF_CloseYesterday']
offsetMapReverse = {v:k for k,v in offsetMap.items()}

# 交易所类型映射
exchangeMap = {}
exchangeMap[EXCHANGE_CFFEX] = 'CFFEX'
exchangeMap[EXCHANGE_SHFE] = 'SHFE'
exchangeMap[EXCHANGE_CZCE] = 'CZCE'
exchangeMap[EXCHANGE_DCE] = 'DCE'
exchangeMap[EXCHANGE_UNKNOWN] = ''
exchangeMapReverse = {v:k for k,v in exchangeMap.items()}

# 持仓类型映射
posiDirectionMap = {}
posiDirectionMap[DIRECTION_NET] = defineDict["THOST_FTDC_PD_Net"]
posiDirectionMap[DIRECTION_LONG] = defineDict["THOST_FTDC_PD_Long"]
posiDirectionMap[DIRECTION_SHORT] = defineDict["THOST_FTDC_PD_Short"]
posiDirectionMapReverse = {v:k for k,v in posiDirectionMap.items()}


class CtpGateway(BasicGateway):
    """CTP Gateway, 未初始化的版本，必须_inited"""

    def __init__(self, mainEngine, gatewayName='CTP'):
        super(CtpGateway, self).__init__(mainEngine, gatewayName)

        self.mdApi = CtpMdApi(self)     # 行情API
        self.tdApi = CtpTdApi(self)     # 交易API

        self.position = {}
        self.orderBuffer = OrderBuffer(mainEngine, self)
    
    @property
    def mdConnected(self):
        return self.mdApi.loginStatus and self.mdApi.connectionStatus

    @property
    def tdConnected(self):
        return self.tdApi.loginStatus and self.tdApi.connectionStatus

    def _onPosition(self, position):
        if self.position.get(position.symbol) is None:
            self.position[position.symbol] = {}
            self.position[position.symbol][DIRECTION_LONG] = PositionData(symbol=position.symbol, direction=DIRECTION_LONG)
            self.position[position.symbol][DIRECTION_SHORT] = PositionData(symbol=position.symbol, direction=DIRECTION_SHORT)
        self.position[position.symbol][position.direction] = position

    def connect(self):

        # 载入json文件
        fileName = self.gatewayName + '_connect.json'
        fileName = os.getcwd() + '/ctpGate/' + fileName

        try:
            f = file(fileName)
        except IOError:
            self.mainEngine.logEvent.emit(LogData(u'读取连接配置出错，请检查'))
            return

        # 解析json文件
        setting = json.load(f)
        try:
            userID = str(setting['userID'])
            password = str(setting['password'])
            brokerID = str(setting['brokerID'])
            tdAddress = str(setting['tdAddress'])
            mdAddress = str(setting['mdAddress'])
        except KeyError:
            self.mainEngine.logEvent.emit(LogData(u'连接配置缺少字段，请检查'))
            return

        # 创建行情和交易接口对象
        self.mdApi.connect(userID, password, brokerID, mdAddress)
        self.tdApi.connect(userID, password, brokerID, tdAddress)

    def subscribe(self, subscribeReq):
        """订阅行情"""
        self.mdApi.subscribe(subscribeReq)

    def sendOrder(self, orderReq):
        """发单"""
        return self.tdApi.sendOrder(orderReq)

    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.tdApi.cancelOrder(cancelOrderReq)

    def qryAccount(self):
        """查询账户资金"""
        self.tdApi.qryAccount()

    def qryPosition(self):
        """查询持仓"""
        self.tdApi.qryPosition()
        self.mainEngine.logEvent.emit(LogData(u'$$$ 正在查询持仓，等待接收持仓数据 $$$'))

    def qryInstrument(self):
        self.tdApi.qryInstrument()

    def close(self):
        """关闭"""
        if self.mdConnected:
            self.mdApi.close()
        if self.tdConnected:
            self.tdApi.close()

    def getOffset(self, pos, volToClose, method='TodayFirst'):
        """
        输入参数pos为需要平仓的方向。若下单为买入，pos为空头仓位。
        method: 可选 TodayFirst, YestodayFirst, Open. 对于非上期所，前两项等价
        """
        # 默认OPEN
        offset = OFFSET_OPEN
        # 上期所，使用平今和平仓
        if self.getContractInfo(pos.symbol, 'exchange') == EXCHANGE_SHFE:
            if method == 'TodayFirst':
                if pos.tdPosition - pos.tdFrozen >= volToClose:
                    offset = OFFSET_CLOSETODAY
                elif pos.ydPosition - pos.ydFrozen >= volToClose:
                    offset = OFFSET_CLOSE
            elif method == 'YestodayFirst':
                if pos.ydPosition - pos.ydFrozen >= volToClose:
                    offset = OFFSET_CLOSE
                elif pos.tdPosition - pos.tdFrozen >= volToClose:
                    offset = OFFSET_CLOSETODAY
        # 非上期所，使用平仓
        else:
            if method == 'TodayFirst' or method == 'YestodayFirst':
                if pos.position - pos.frozen >= volToClose:
                    offset = OFFSET_CLOSE
        return offset


class CtpMdApi(MdApi):
    """CTP行情API实现"""

    def __init__(self, gateway):
        """Constructor"""
        super(CtpMdApi, self).__init__()

        self.gateway = gateway                  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称

        self.reqID = EMPTY_INT              # 操作请求编号

        self.connectionStatus = False       # 连接状态
        self.loginStatus = False            # 登录状态

        self.subscribedSymbols = set()      # 已订阅合约代码

        self.userID = EMPTY_STRING          # 账号
        self.password = EMPTY_STRING        # 密码
        self.brokerID = EMPTY_STRING        # 经纪商代码
        self.address = EMPTY_STRING         # 服务器地址

    def onFrontConnected(self):
        """服务器连接"""
        self.connectionStatus = True

        self.gateway.mainEngine.logEvent.emit(LogData(u'行情服务器连接成功'))

        self.login()

    def onFrontDisconnected(self, n):
        """服务器断开"""
        self.connectionStatus = False
        self.loginStatus = False

        self.gateway.mainEngine.logEvent.emit(LogData(u'行情服务器连接断开'))
    
    def onHeartBeatWarning(self, n):
        """心跳报警"""
        # 因为API的心跳报警比较常被触发，且与API工作关系不大，因此选择忽略
        pass

    def onRspError(self, error, n, last):
        """错误回报"""
        err = ErrorData()
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onRspUserLogin(self, data, error, n, last):
        """登陆回报"""
        # 如果登录成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = True

            self.gateway.mainEngine.logEvent.emit(LogData(u'行情服务器登录完成'))

            # 重新订阅之前订阅的合约
            for subscribeReq in self.subscribedSymbols:
                self.subscribe(subscribeReq)

        # 否则，推送错误信息
        else:
            err = ErrorData()
            err.errorID = error['ErrorID']
            err.errorMsg = error['ErrorMsg'].decode('gbk')
            self.gateway.mainEngine.errorEvent.emit(err)

    def onRspUserLogout(self, data, error, n, last):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = False

            self.gateway.mainEngine.logEvent.emit(LogData(u'行情服务器登出完成'))

        # 否则，推送错误信息
        else:
            err = ErrorData()
            err.errorID = error['ErrorID']
            err.errorMsg = error['ErrorMsg'].decode('gbk')
            self.gateway.mainEngine.errorEvent.emit(err)

    def onRspSubMarketData(self, data, error, n, last):
        """订阅合约回报"""

        if error['ErrorID'] == 0:
            self.gateway.mainEngine.logEvent.emit(LogData(u'订阅合约完成  {0}'.format(data)))

        else:
            err = ErrorData()
            err.errorID = error['ErrorID']
            err.errorMsg = error['ErrorMsg'].decode('gbk')
            self.gateway.mainEngine.errorEvent.emit(err)

    def onRspUnSubMarketData(self, data, error, n, last):
        """退订合约回报"""
        pass

    def onRtnDepthMarketData(self, data):
        """行情推送"""
        tick = TickData()

        tick.symbol = data['InstrumentID']
        tick.exchange = exchangeMapReverse.get(data['ExchangeID'], u'未知')
        tick.vtSymbol = tick.symbol #'.'.join([tick.symbol, EXCHANGE_UNKNOWN])

        tick.lastPrice = data['LastPrice']
        tick.volume = data['Volume']
        tick.openInterest = data['OpenInterest']
        tick.time = '.'.join([data['UpdateTime'], str(data['UpdateMillisec']/100)])
        tick.date = data['TradingDay']

        tick.openPrice = data['OpenPrice']
        tick.highPrice = data['HighestPrice']
        tick.lowPrice = data['LowestPrice']
        tick.preClosePrice = data['PreClosePrice']

        tick.upperLimit = data['UpperLimitPrice']
        tick.lowerLimit = data['LowerLimitPrice']

        # CTP只有一档行情
        tick.bidPrice1 = data['BidPrice1']
        tick.bidVolume1 = data['BidVolume1']
        tick.askPrice1 = data['AskPrice1']
        tick.askVolume1 = data['AskVolume1']

        self.gateway.mainEngine.tickDataEvent.emit(tick)

    def onRspSubForQuoteRsp(self, data, error, n, last):
        """订阅期权询价"""
        pass

    def onRspUnSubForQuoteRsp(self, data, error, n, last):
        """退订期权询价"""
        pass

    def onRtnForQuoteRsp(self, data):
        """期权询价推送"""
        pass

    def connect(self, userID, password, brokerID, address):
        """初始化连接"""
        self.userID = userID                # 账号
        self.password = password            # 密码
        self.brokerID = brokerID            # 经纪商代码
        self.address = address              # 服务器地址

        # 如果尚未建立服务器连接，则进行连接
        if not self.connectionStatus:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            path = os.getcwd() + '/temp/' + self.gatewayName + '/'
            if not os.path.exists(path):
                os.makedirs(path)
            self.createFtdcMdApi(path)

            # 注册服务器地址
            self.registerFront(self.address)

            # 初始化连接，成功会调用onFrontConnected
            self.init()

        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.loginStatus:
                self.login()

    def subscribe(self, subscribeReq):
        """订阅合约"""
        # 这里的设计是，如果尚未登录就调用了订阅方法
        # 则先保存订阅请求，登录完成后会自动订阅
        if self.loginStatus:
            self.subscribeMarketData(str(subscribeReq.symbol))
        self.subscribedSymbols.add(subscribeReq)

    def login(self):
        """登录"""
        # 如果填入了用户名密码等，则登录
        if self.userID and self.password and self.brokerID:
            req = {}
            req['UserID'] = self.userID
            req['Password'] = self.password
            req['BrokerID'] = self.brokerID
            self.reqID += 1
            self.reqUserLogin(req, self.reqID)

    def close(self):
        """关闭"""
        self.exit()


class CtpTdApi(TdApi):
    """CTP交易API实现"""

    def __init__(self, gateway):
        """API对象的初始化函数"""
        super(CtpTdApi, self).__init__()

        self.gateway = gateway                  # gateway对象
        self.gatewayName = gateway.gatewayName  # gateway对象名称

        self.reqID = EMPTY_INT              # 操作请求编号
        self.orderRef = EMPTY_INT           # 订单编号

        self.connectionStatus = False       # 连接状态
        self.loginStatus = False            # 登录状态

        self.userID = EMPTY_STRING          # 账号
        self.password = EMPTY_STRING        # 密码
        self.brokerID = EMPTY_STRING        # 经纪商代码
        self.address = EMPTY_STRING         # 服务器地址

        self.frontID = EMPTY_INT            # 前置机编号
        self.sessionID = EMPTY_INT          # 会话编号

        self.posBufferDict = {}             # 缓存持仓数据的字典


    def onFrontConnected(self):
        """服务器连接"""
        self.connectionStatus = True

        self.gateway.mainEngine.logEvent.emit(LogData(u'交易服务器连接成功'))

        self.login()

    def onFrontDisconnected(self, n):
        """服务器断开"""
        self.connectionStatus = False
        self.loginStatus = False

        self.gateway.mainEngine.logEvent.emit(LogData(u'交易服务器连接断开'))
    
    def onHeartBeatWarning(self, n):
        """"""
        pass

    def onRspAuthenticate(self, data, error, n, last):
        """"""
        pass

    def onRspUserLogin(self, data, error, n, last):
        """登陆回报"""
        # 如果登录成功，推送日志信息
        if error['ErrorID'] == 0:
            self.frontID = str(data['FrontID'])
            self.sessionID = str(data['SessionID'])
            self.loginStatus = True

            self.gateway.mainEngine.logEvent.emit(LogData(u'交易服务器登录完成'))

            # 确认结算信息
            req = {}
            req['BrokerID'] = self.brokerID
            req['InvestorID'] = self.userID
            self.reqID += 1
            self.reqSettlementInfoConfirm(req, self.reqID)
        # 否则，推送错误信息
        else:
            err = ErrorData()
            err.gatewayName = self.gatewayName
            err.errorID = error['ErrorID']
            err.errorMsg = error['ErrorMsg'].decode('gbk')
            self.gateway.mainEngine.errorEvent.emit(err)

    def onRspUserLogout(self, data, error, n, last):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if error['ErrorID'] == 0:
            self.loginStatus = False

            self.gateway.mainEngine.logEvent.emit(LogData(u'交易服务器登出完成'))
        # 否则，推送错误信息
        else:
            err = ErrorData()
            err.gatewayName = self.gatewayName
            err.errorID = error['ErrorID']
            err.errorMsg = error['ErrorMsg'].decode('gbk')
            self.gateway.mainEngine.errorEvent.emit(err)

    def onRspUserPasswordUpdate(self, data, error, n, last):
        """"""
        pass

    def onRspTradingAccountPasswordUpdate(self, data, error, n, last):
        """"""
        pass

    def onRspOrderInsert(self, data, error, n, last):
        """发单错误（柜台）"""
        err = ErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onRspParkedOrderInsert(self, data, error, n, last):
        """"""
        pass

    def onRspOrderAction(self, data, error, n, last):
        """撤单错误（柜台）"""
        err = ErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onRspQueryMaxOrderVolume(self, data, error, n, last):
        """"""
        pass

    def onRspSettlementInfoConfirm(self, data, error, n, last):
        """确认结算信息回报"""
        self.gateway.mainEngine.logEvent.emit(LogData(u'结算信息确认完成'))

        # 查询合约代码
        self.reqID += 1
        self.reqQryInstrument({}, self.reqID)

    def onRspRemoveParkedOrder(self, data, error, n, last):
        """"""
        pass

    def onRspRemoveParkedOrderAction(self, data, error, n, last):
        """"""
        pass

    def onRspExecOrderInsert(self, data, error, n, last):
        """"""
        pass

    def onRspExecOrderAction(self, data, error, n, last):
        """"""
        pass

    def onRspForQuoteInsert(self, data, error, n, last):
        """"""
        pass

    def onRspQuoteInsert(self, data, error, n, last):
        """"""
        pass

    def onRspQuoteAction(self, data, error, n, last):
        """"""
        pass

    def onRspQryOrder(self, data, error, n, last):
        """"""
        pass

    def onRspQryTrade(self, data, error, n, last):
        """"""
        pass

    def onRspQryInvestorPosition(self, data, error, n, last):
        """持仓查询回报"""
        # 获取缓存字典中的持仓缓存，若无则创建并初始化
        positionName = '.'.join([data['InstrumentID'], data['PosiDirection']])

        if positionName in self.posBufferDict:
            posBuffer = self.posBufferDict[positionName]
        else:
            posBuffer = PositionBuffer(data, self.gatewayName, self.gateway)
            self.posBufferDict[positionName] = posBuffer

        # 更新持仓缓存，并获取VT系统中持仓对象的返回值
        pos = posBuffer.updateBuffer(data)
        self.gateway.mainEngine.positionEvent.emit(pos)

    def onRspQryTradingAccount(self, data, error, n, last):
        """资金账户查询回报"""
        account = AccountData()
        account.gatewayName = self.gatewayName

        # 账户代码
        account.accountID = data['AccountID']
        account.vtAccountID = '.'.join([self.gatewayName, account.accountID])

        # 数值相关
        account.preBalance = data['PreBalance']
        account.available = data['Available']
        account.commission = data['Commission']
        account.margin = data['CurrMargin']
        account.closeProfit = data['CloseProfit']
        account.positionProfit = data['PositionProfit']

        # 这里的balance和快期中的账户不确定是否一样，需要测试
        account.balance = (data['PreBalance'] - data['PreCredit'] - data['PreMortgage'] +
                           data['Mortgage'] - data['Withdraw'] + data['Deposit'] +
                           data['CloseProfit'] + data['PositionProfit'] + data['CashIn'] -
                           data['Commission'])

        # 推送
        self.gateway.mainEngine.accountEvent.emit(account)

    def onRspQryInvestor(self, data, error, n, last):
        """投资者查询回报"""
        pass

    def onRspQryTradingCode(self, data, error, n, last):
        """"""
        pass

    def onRspQryInstrumentMarginRate(self, data, error, n, last):
        """"""
        pass

    def onRspQryInstrumentCommissionRate(self, data, error, n, last):
        """"""
        pass

    def onRspQryExchange(self, data, error, n, last):
        """"""
        pass

    def onRspQryProduct(self, data, error, n, last):
        """"""
        pass

    def onRspQryInstrument(self, data, error, n, last):
        """合约查询回报"""
        contract = ContractData()
        contract.gatewayName = self.gatewayName

        contract.symbol = data['InstrumentID']
        contract.exchange = exchangeMapReverse[data['ExchangeID']]
        contract.vtSymbol = contract.symbol #'.'.join([contract.symbol, contract.exchange])
        contract.name = data['InstrumentName'].decode('GBK')

        # 合约数值
        contract.size = data['VolumeMultiple']
        contract.priceTick = data['PriceTick']
        contract.strikePrice = data['StrikePrice']
        contract.underlyingSymbol = data['UnderlyingInstrID']

        # 合约类型
        if data['ProductClass'] == '1':
            contract.productClass = PRODUCT_FUTURES
        elif data['ProductClass'] == '2':
            contract.productClass = PRODUCT_OPTION
        elif data['ProductClass'] == '3':
            contract.productClass = PRODUCT_COMBINATION
        else:
            contract.productClass = PRODUCT_UNKNOWN

        # 期权类型
        if data['OptionsType'] == '1':
            contract.optionType = OPTION_CALL
        elif data['OptionsType'] == '2':
            contract.optionType = OPTION_PUT

        # 推送
        self.gateway.mainEngine.contractEvent.emit(contract)

        if last:
            self.gateway.mainEngine.logEvent.emit(LogData(u'交易合约信息获取完成'))

    def onRspQryDepthMarketData(self, data, error, n, last):
        """"""
        pass

    def onRspQrySettlementInfo(self, data, error, n, last):
        """查询结算信息回报"""
        pass

    def onRspQryTransferBank(self, data, error, n, last):
        """"""
        pass

    def onRspQryInvestorPositionDetail(self, data, error, n, last):
        """"""
        pass

    def onRspQryNotice(self, data, error, n, last):
        """"""
        pass

    def onRspQrySettlementInfoConfirm(self, data, error, n, last):
        """"""
        pass

    def onRspQryInvestorPositionCombineDetail(self, data, error, n, last):
        """"""
        pass

    def onRspQryCFMMCTradingAccountKey(self, data, error, n, last):
        """"""
        pass

    def onRspQryEWarrantOffset(self, data, error, n, last):
        """"""
        pass

    def onRspQryInvestorProductGroupMargin(self, data, error, n, last):
        """"""
        pass

    def onRspQryExchangeMarginRate(self, data, error, n, last):
        """"""
        pass

    def onRspQryExchangeMarginRateAdjust(self, data, error, n, last):
        """"""
        pass

    def onRspQryExchangeRate(self, data, error, n, last):
        """"""
        pass

    def onRspQrySecAgentACIDMap(self, data, error, n, last):
        """"""
        pass

    def onRspQryOptionInstrTradeCost(self, data, error, n, last):
        """"""
        pass

    def onRspQryOptionInstrCommRate(self, data, error, n, last):
        """"""
        pass

    def onRspQryExecOrder(self, data, error, n, last):
        """"""
        pass

    def onRspQryForQuote(self, data, error, n, last):
        """"""
        pass

    def onRspQryQuote(self, data, error, n, last):
        """"""
        pass

    def onRspQryTransferSerial(self, data, error, n, last):
        """"""
        pass

    def onRspQryAccountregister(self, data, error, n, last):
        """"""
        pass

    def onRspError(self, error, n, last):
        """错误回报"""
        err = ErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onRtnOrder(self, data):
        """报单回报"""
        # 更新最大报单编号
        newref = data['OrderRef']
        self.orderRef = max(self.orderRef, int(newref))

        # 创建报单数据对象
        order = OrderData()
        order.gatewayName = self.gatewayName

        # 保存代码和报单号
        order.symbol = data['InstrumentID']
        order.exchange = exchangeMapReverse[data['ExchangeID']]
        order.vtSymbol = order.symbol #'.'.join([order.symbol, order.exchange])

        order.orderID = data['OrderRef']

        # 方向
        if data['Direction'] == '0':
            order.direction = DIRECTION_LONG
        elif data['Direction'] == '1':
            order.direction = DIRECTION_SHORT
        else:
            order.direction = DIRECTION_UNKNOWN

        # 开平
        if data['CombOffsetFlag'] == '0':
            order.offset = OFFSET_OPEN
        elif data['CombOffsetFlag'] == '1':
            order.offset = OFFSET_CLOSE
        else:
            order.offset = OFFSET_UNKNOWN

        # 状态
        if data['OrderStatus'] == '0':
            order.status = STATUS_ALLTRADED
        elif data['OrderStatus'] == '1':
            order.status = STATUS_PARTTRADED
        elif data['OrderStatus'] == '3':
            order.status = STATUS_NOTTRADED
        elif data['OrderStatus'] == '5':
            order.status = STATUS_CANCELLED
            # -----------撤单事件-----------
            self.gateway.mainEngine.cancelEvent.emit(order)
            # -----------------------------
        else:
            order.status = STATUS_UNKNOWN

        # 价格、报单量等数值
        order.price = data['LimitPrice']
        order.totalVolume = data['VolumeTotalOriginal']
        order.tradedVolume = data['VolumeTraded']
        order.orderTime = data['InsertTime']
        order.cancelTime = data['CancelTime']
        order.frontID = data['FrontID']
        order.sessionID = data['SessionID']

        # CTP的报单号一致性维护需要基于frontID, sessionID, orderID三个字段
        # 但在本接口设计中，已经考虑了CTP的OrderRef的自增性，避免重复
        # 唯一可能出现OrderRef重复的情况是多处登录并在非常接近的时间内（几乎同时发单）
        # 考虑到VtTrader的应用场景，认为以上情况不会构成问题
        order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

        # 推送
        self.gateway.mainEngine.orderEvent.emit(order)

    def onRtnTrade(self, data):
        """成交回报"""
        # 创建报单数据对象
        trade = TradeData()
        trade.gatewayName = self.gatewayName

        # 保存代码和报单号
        trade.symbol = data['InstrumentID']
        trade.exchange = exchangeMapReverse[data['ExchangeID']]
        trade.vtSymbol = trade.symbol #'.'.join([trade.symbol, trade.exchange])

        trade.tradeID = data['TradeID']
        trade.vtTradeID = '.'.join([self.gatewayName, trade.tradeID])

        trade.orderID = data['OrderRef']
        trade.vtOrderID = '.'.join([self.gatewayName, trade.orderID])

        # 方向
        trade.direction = directionMapReverse.get(data['Direction'], '')

        # 开平
        trade.offset = offsetMapReverse.get(data['OffsetFlag'], '')

        # 价格、报单量等数值
        trade.price = data['Price']
        trade.volume = data['Volume']
        trade.tradeTime = data['TradeTime']

        # 推送
        self.gateway.mainEngine.tradeEvent.emit(trade)

    def onErrRtnOrderInsert(self, data, error):
        """发单错误回报（交易所）"""
        err = ErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onErrRtnOrderAction(self, data, error):
        """撤单错误回报（交易所）"""
        err = ErrorData()
        err.gatewayName = self.gatewayName
        err.errorID = error['ErrorID']
        err.errorMsg = error['ErrorMsg'].decode('gbk')
        self.gateway.mainEngine.errorEvent.emit(err)

    def onRtnInstrumentStatus(self, data):
        """"""
        pass

    def onRtnTradingNotice(self, data):
        """"""
        pass

    def onRtnErrorConditionalOrder(self, data):
        """"""
        pass

    def onRtnExecOrder(self, data):
        """"""
        pass

    def onErrRtnExecOrderInsert(self, data, error):
        """"""
        pass

    def onErrRtnExecOrderAction(self, data, error):
        """"""
        pass

    def onErrRtnForQuoteInsert(self, data, error):
        """"""
        pass

    def onRtnQuote(self, data):
        """"""
        pass

    def onErrRtnQuoteInsert(self, data, error):
        """"""
        pass

    def onErrRtnQuoteAction(self, data, error):
        """"""
        pass

    def onRtnForQuoteRsp(self, data):
        """"""
        pass

    def onRspQryContractBank(self, data, error, n, last):
        """"""
        pass

    def onRspQryParkedOrder(self, data, error, n, last):
        """"""
        pass

    def onRspQryParkedOrderAction(self, data, error, n, last):
        """"""
        pass

    def onRspQryTradingNotice(self, data, error, n, last):
        """"""
        pass

    def onRspQryBrokerTradingParams(self, data, error, n, last):
        """"""
        pass

    def onRspQryBrokerTradingAlgos(self, data, error, n, last):
        """"""
        pass

    def onRtnFromBankToFutureByBank(self, data):
        """"""
        pass

    def onRtnFromFutureToBankByBank(self, data):
        """"""
        pass

    def onRtnRepealFromBankToFutureByBank(self, data):
        """"""
        pass

    def onRtnRepealFromFutureToBankByBank(self, data):
        """"""
        pass

    def onRtnFromBankToFutureByFuture(self, data):
        """"""
        pass

    def onRtnFromFutureToBankByFuture(self, data):
        """"""
        pass

    def onRtnRepealFromBankToFutureByFutureManual(self, data):
        """"""
        pass

    def onRtnRepealFromFutureToBankByFutureManual(self, data):
        """"""
        pass

    def onRtnQueryBankBalanceByFuture(self, data):
        """"""
        pass

    def onErrRtnBankToFutureByFuture(self, data, error):
        """"""
        pass

    def onErrRtnFutureToBankByFuture(self, data, error):
        """"""
        pass

    def onErrRtnRepealBankToFutureByFutureManual(self, data, error):
        """"""
        pass

    def onErrRtnRepealFutureToBankByFutureManual(self, data, error):
        """"""
        pass

    def onErrRtnQueryBankBalanceByFuture(self, data, error):
        """"""
        pass

    def onRtnRepealFromBankToFutureByFuture(self, data):
        """"""
        pass

    def onRtnRepealFromFutureToBankByFuture(self, data):
        """"""
        pass

    def onRspFromBankToFutureByFuture(self, data, error, n, last):
        """"""
        pass

    def onRspFromFutureToBankByFuture(self, data, error, n, last):
        """"""
        pass

    def onRspQueryBankAccountMoneyByFuture(self, data, error, n, last):
        """"""
        pass

    def onRtnOpenAccountByBank(self, data):
        """"""
        pass

    def onRtnCancelAccountByBank(self, data):
        """"""
        pass

    def onRtnChangeAccountByBank(self, data):
        """"""
        pass

    def connect(self, userID, password, brokerID, address):
        """初始化连接"""
        self.userID = userID                # 账号
        self.password = password            # 密码
        self.brokerID = brokerID            # 经纪商代码
        self.address = address              # 服务器地址

        # 如果尚未建立服务器连接，则进行连接
        if not self.connectionStatus:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            path = os.getcwd() + '/temp/' + self.gatewayName + '/'
            if not os.path.exists(path):
                os.makedirs(path)
            self.createFtdcTraderApi(path)

            # 注册服务器地址
            self.registerFront(self.address)

            # 初始化连接，成功会调用onFrontConnected
            self.init()

        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.loginStatus:
                self.login()

    def login(self):
        """连接服务器"""
        # 如果填入了用户名密码等，则登录
        if self.userID and self.password and self.brokerID:
            req = {}
            req['UserID'] = self.userID
            req['Password'] = self.password
            req['BrokerID'] = self.brokerID
            self.reqID += 1
            self.reqUserLogin(req, self.reqID)

    def qryAccount(self):
        """查询账户"""
        self.reqID += 1
        self.reqQryTradingAccount({}, self.reqID)

    def qryPosition(self):
        """查询持仓"""
        self.reqID += 1
        req = {}
        req['BrokerID'] = self.brokerID
        req['InvestorID'] = self.userID
        self.reqQryInvestorPosition(req, self.reqID)

    def qryInstrument(self):
        self.reqID += 1
        self.reqQryInstrument({}, self.reqID)

    def sendOrder(self, orderReq):
        """发单"""
        self.reqID += 1
        self.orderRef += 1

        req = {}

        req['InstrumentID'] = orderReq.symbol
        req['LimitPrice'] = orderReq.price
        req['VolumeTotalOriginal'] = orderReq.volume

        # 下面如果由于传入的类型本接口不支持，则会返回空字符串
        req['OrderPriceType'] = priceTypeMap.get(orderReq.priceType, '')
        req['Direction'] = directionMap.get(orderReq.direction, '')
        req['CombOffsetFlag'] = offsetMap.get(orderReq.offset, '')

        req['OrderRef'] = str(self.orderRef)
        req['InvestorID'] = self.userID
        req['UserID'] = self.userID
        req['BrokerID'] = self.brokerID

        req['CombHedgeFlag'] = defineDict['THOST_FTDC_HF_Speculation']       # 投机单
        req['ContingentCondition'] = defineDict['THOST_FTDC_CC_Immediately'] # 立即发单
        req['ForceCloseReason'] = defineDict['THOST_FTDC_FCC_NotForceClose'] # 非强平
        req['IsAutoSuspend'] = 0                                             # 非自动挂起
        req['TimeCondition'] = defineDict['THOST_FTDC_TC_GFD']               # 今日有效
        req['VolumeCondition'] = defineDict['THOST_FTDC_VC_AV']              # 任意成交量
        req['MinVolume'] = 1                                                 # 最小成交量为1

        # 判断FAK和FOK
        if orderReq.priceType == PRICETYPE_FAK:
            req['OrderPriceType'] = defineDict["THOST_FTDC_OPT_LimitPrice"]
            req['TimeCondition'] = defineDict['THOST_FTDC_TC_IOC']
            req['VolumeCondition'] = defineDict['THOST_FTDC_VC_AV']
        if orderReq.priceType == PRICETYPE_FOK:
            req['OrderPriceType'] = defineDict["THOST_FTDC_OPT_LimitPrice"]
            req['TimeCondition'] = defineDict['THOST_FTDC_TC_IOC']
            req['VolumeCondition'] = defineDict['THOST_FTDC_VC_CV']

        self.reqOrderInsert(req, self.reqID)

        # 返回订单号（字符串），便于某些算法进行动态管理
        vtOrderID = '.'.join([self.gatewayName, str(self.orderRef)])
        return vtOrderID

    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        self.reqID += 1

        req = {}

        req['InstrumentID'] = cancelOrderReq.symbol
        req['ExchangeID'] = cancelOrderReq.exchange
        req['OrderRef'] = cancelOrderReq.orderID
        req['FrontID'] = cancelOrderReq.frontID
        req['SessionID'] = cancelOrderReq.sessionID

        req['ActionFlag'] = defineDict['THOST_FTDC_AF_Delete']
        req['BrokerID'] = self.brokerID
        req['InvestorID'] = self.userID

        self.reqOrderAction(req, self.reqID)

    def close(self):
        """关闭"""
        self.exit()

class PositionBuffer(object):
    """用来缓存持仓的数据，处理上期所的数据返回分今昨的问题"""

    #----------------------------------------------------------------------
    def __init__(self, data, gatewayName, gateway):
        """Constructor"""
        self.gateway = gateway

        self.symbol = data['InstrumentID']
        self.direction = posiDirectionMapReverse.get(data['PosiDirection'], '')

        self.todayPosition = EMPTY_INT
        self.ydPosition = EMPTY_INT
        self.todayPositionCost = EMPTY_FLOAT
        self.ydPositionCost = EMPTY_FLOAT

        # 通过提前创建持仓数据对象并重复使用的方式来降低开销
        pos = PositionData()
        pos.symbol = self.symbol
        pos.vtSymbol = self.symbol
        pos.gatewayName = gatewayName
        pos.direction = self.direction
        pos.vtPositionName = '.'.join([pos.vtSymbol, pos.direction])
        self.pos = pos

    #----------------------------------------------------------------------
    def updateBuffer(self, data):
        """更新缓存，返回更新后的持仓数据"""

        # 上期所，昨仓和今仓分在两条记录，Frozen也要分开记录
        if self.gateway.getContractInfo(data['InstrumentID'], 'exchange') == EXCHANGE_SHFE:
            if data['TodayPosition']:
                self.todayPosition = data['Position']
                self.todayPositionCost = data['PositionCost']
                self.pos.tdFrozen = data['ShortFrozen'] if self.direction == DIRECTION_LONG else data['LongFrozen']
            elif data['YdPosition']:
                self.ydPosition = data['Position']
                self.ydPositionCost = data['PositionCost']
                self.pos.ydFrozen = data['ShortFrozen'] if self.direction == DIRECTION_LONG else data['LongFrozen']
            self.positionCost = self.todayPositionCost + self.ydPositionCost
            self.pos.position = self.todayPosition + self.ydPosition
        # 非上期所，在一条记录里
        else:
            self.todayPosition = data['TodayPosition']
            self.ydPosition = data['YdPosition']
            self.pos.ydFrozen = data['ShortFrozen'] if self.direction == DIRECTION_LONG else data['LongFrozen']
            self.pos.position = data['Position']
            self.positionCost = data['PositionCost']

        self.pos.ydPosition = self.ydPosition

        # 如果手头还有持仓，则通过加权平均方式计算持仓均价
        if self.todayPosition or self.ydPosition:
            self.pos.price = ((self.positionCost) /
                              ((self.todayPosition + self.ydPosition) *
                                self.gateway.getContractInfo(data['InstrumentID'], 'size')))
        # 否则价格为0
        else:
            self.pos.price = 0

        return copy(self.pos)




