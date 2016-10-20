# A_simple_algo_trading_system
一个练手的小项目，单进程版，受Python的GIL限制，不能运行较多策略。多进程版本以及交易算法和策略是在实习期间编写，因此没有开源。

使用开源项目[vn.py](https://github.com/vnpy/vnpy)的CTP API的python封装，基于vn.py的`CTP gateway`模块进行了修改，自行设计了`ComplexOrder`模块。

### 使用方法

1. 根据[vn.py](https://github.com/vnpy/vnpy)的说明配置运行环境、交易前置、行情前置和CTP账号。

2. 打开界面时会等待几秒，此时在自动连接CTP。若看到持仓信息，则连接完成；若显示没有查到持仓信息，则需要点击`系统 - 连接CTP`再次连接。

3. 点击`策略 - TWAP ORDER`可开启`TWAP ORDER`控制面板，可以进行各项操作。`确认参数`操作不是必需的，在`下单`时也会自动读取各项参数。

4. `查询状态`界面不会自动更新，需要手动点击`查询状态`才会更新最新状态。