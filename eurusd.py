import time
from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector

print("Initializing connector")
_zmq = DWX_ZeroMQ_Connector()

print("Subscribing for prices")
_zmq._DWX_MTX_SUBSCRIBE_MARKETDATA_('EURUSDm')
_zmq._DWX_MTX_SEND_TRACKPRICES_REQUEST_(['EURUSDm'])

_zmq._DWX_MTX_SUBSCRIBE_MARKETDATA_('EURAUDm')
_zmq._DWX_MTX_SEND_TRACKPRICES_REQUEST_(['EURAUDm'])

#time.sleep(5)
#print("show prices")
#_zmq._Market_Data_DB['EURUSDc']

print("getting all orders")
_zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
input()

#_zmq._DWX_MTX_UNSUBSCRIBE_MARKETDATA_('EURUSDc')

'''print("Making order")
_my_trade = _zmq._generate_default_order_dict()
_my_trade['_symbol']='EURUSDc'

_zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)
input()

'''

