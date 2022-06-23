import time
import json
from bs4 import BeautifulSoup
from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from tradingview import tradingPairs



if __name__ == '__main__':
    
    _zmq = DWX_ZeroMQ_Connector()
    _zmq._DWX_MTX_CLOSE_TRADES_BY_MAGIC_(123456)
    open_trades=_zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
    print(open_trades)