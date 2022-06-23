from time import sleep
from datetime import datetime
import json
from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
import random
import signal
import configparser
import psycopg2
from icecream import ic


# Register an handler for the timeout
def handler(signum, frame):
     print("Forever is over!")
     raise Exception("end of time")


class openTrades():

    def __init__(self,
                _zmq,
                _open_trades=None,
                _delay=2,
                _wbreak=12,
                _ws = datetime.now()
        ):
        self.open_trades=_open_trades
        self.delay=_delay
        self.wbreak=_wbreak
        self.ws=_ws
        self.zmq=_zmq


    def getAllOpenTrades(self):
        ws=datetime.now()
        self.zmq._set_response_(None)
        self.zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()

        while self.zmq._valid_response_('zmq') == False:

            sleep(self.delay)

            if (datetime.now() - ws).total_seconds() > (self.delay * self.wbreak):
                return 0


            # If data received, return DataFrame
            if self.zmq._valid_response_('zmq'):
                _response = self.zmq._get_response_()
                return _response['_trades']


    def getOpenTrade(self):
        return 0

class order():


    def __init__(self, _zmq, validSymbols=[
                        'AUDUSDm',
                        'EURUSDm',
                        'GBPUSDm',
                        'USDCHFm',
                        'USDJPYm',
                        'AUDCHFm',
                        'CHFJPYm',
                        'EURGBPm',
                        'EURJPYm'

                     ],
                     oType=['sell', 'buy'],
                     _delay=1,
                     _wbreak=6000,
                     _ws = datetime.now().date(),
                     symbolSuffix='m'
                     ):
        self.zmq=_zmq
        self.validSymbols=[]
        for symbol in validSymbols:
            self.validSymbols.append(symbol+symbolSuffix)
        self.oType=oType
        self.delay=_delay
        self.wbreak=_wbreak
        self.ws=_ws



    def printValidSymbols(self):
        print(self.validSymbols)

    def returnValidSymbols(self):
        return self.validSymbols

    def symbolValidate(self, symbol):
        return True if symbol in self.validSymbols else False

    def typeValidate(self, type):
        return True if type in self.oType else False



    def openOrder(self, symbol, otype = 1, comment = '', lots = 0.01, sl = 50000, tp = 1000):

         # Reset data output
        self.zmq._set_response_(None)
        _my_trade = self.zmq._generate_default_order_dict()

        _my_trade['_symbol']=symbol
        _my_trade['_type']=otype
        #_my_trade['_type']=random.randrange(0, 2) #random trading
        _my_trade['_SL']=sl
        _my_trade['_TP']=tp
        _my_trade['_comment']=comment
        _my_trade['_lots']=lots

        self.zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)


        while self.zmq._valid_response_('zmq') == False:

            sleep(self.delay)
            if (datetime.now().date() - self.ws).total_seconds() > (self.delay * self.wbreak):
                break

            # If data received, return DataFrame
            if self.zmq._valid_response_('zmq'):
                _response = self.zmq._get_response_()

                return _response



    def closeOrder(self, order):

        self.zmq._set_response_(None)
        self.zmq._DWX_MTX_CLOSE_TRADE_BY_TICKET_(order)

        while self.zmq._valid_response_('zmq') == False:

            sleep(self.delay)
            if (datetime.now().date() - self.ws).total_seconds() > (self.delay * self.wbreak):
                break

            # If data received, return DataFrame
            if self.zmq._valid_response_('zmq'):
                _response = self.zmq._get_response_()

                return _response


class dataToDB():

    def __init__(self, cur):
        self.cur = cur

    def groupsToDB(self, group):
        self.cur.execute("insert into groups(comment) values ('%s') on conflict (comment) do nothing" % group)
        return 1

    def symbolsToDB(self, symbol):
        self.cur.execute("insert into symbols(symbol) values ('%s') on conflict (symbol) do nothing" % symbol)
        return 1

    def ordersToDB(self, order, symbol, open_proce, loss, group, lots, type):
        self.cur.execute("insert into orders(oid, sid, open_price, loss, gid, tid, lots, is_active) values ('%s', (select sid from symbols where symbol='%s'), %s, %s, (select gid from groups where comment='%s'), %s, %s, 't') on conflict (oid) do update set loss=%s" %  (order, symbol, open_proce, loss, group, type, lots, loss))
        return 1

    def ordersPendingToDB(self, order):
        self.cur.execute("insert into orders_pending values (%s, NOW(), (select psid from pending_status where status='pending'), 0, 0) on conflict (oid, psid, close_num) do update set retries=orders_pending.retries+1" % order)
        return 1

    def ordersPendingFailed(self):
        self.cur.execute("update orders_pending set psid=2, close_num=(select max(close_num)+1 from orders_pending) where retries>10 and psid=1") #1 - pending, 2 - failed
        return 1

    def ordersPendingClosed(self, openOrders):
        self.cur.execute("with rows as (update orders_pending set psid=3, close_num=close_num+1 where psid=1 and oid not in %(ordersList)s returning 1) select * from rows" , {'ordersList': openOrders}) #1 - pending, 2 - failed, 3 - closed
        fetch = self.cur.fetchone()

        if fetch is not None:
            rows=fetch[0]
        else:
            rows=0
        self.cur.execute("update orders set is_active='f' where oid in (select oid from orders_pending where psid=3)")
        return rows

    def statisticsToDb(self):
        self.cur.execute("insert into statistics (               time,                available_balance,               loss_balbance,                oldest_group,               oldest_group_count,               oldest_group_loss,               profit_abs,               loss_abs,               loss_diff,               orders_count_active,               orders_count_closed,               min_loss_group)        values (               NOW(),               (select sum(loss)/3+(select loss from loss_balance)/2 as available_balance from orders where is_active is false),               (select loss as loss_balance from loss_balance),               (select comment from groups where gid=(select min(gid) from orders where is_active is true)),               (select count(*) as oldest_orders_count from orders where gid=(select min(gid) from orders where is_active is true) and is_active is true),               (select sum(loss) as oldest_orders_loss from orders where gid=(select min(gid) from orders where is_active is true) and is_active is true),               (select sum(loss) as profit from orders where is_active is false),               (select sum(loss) as current_loss from orders where is_active is true),               (select (select sum(loss) as profit from orders where is_active is false) + (select sum(loss) as current_loss from orders where is_active is true)),               (select count(*) as count_orders from orders where is_active is true),               (select count(*) as closed_orders from orders where is_active is false),               (select sum(loss) as min_lass from orders where is_active is true group by gid order by 1 desc limit 1)       )")
        return 1


class analyze():

    def __init__(self, cursor, ordersTimeout, takeProfit, stopLoss, orderCountLimit, takeProfitSingle):
        self.cur = cursor
        self.ordersTimeout = ordersTimeout
        self.takeProfit = takeProfit
        self.stopLoss = stopLoss
        self.orderCountLimit = orderCountLimit
        self.takeProfitSingle = takeProfitSingle

    def oldestOrder(self):
        self.cur.execute("select case when (select count(oid) from orders where is_active is true)>%s then 0 when extract(epoch from (now()-max(comment::timestamp)))/%s > 1 then 1 else 0 end from groups;" % (self.orderCountLimit, self.ordersTimeout))
        return self.cur.fetchone()

    def closeOrders(self):
        orderList=[]
        self.cur.execute("select distinct(oid) from (select oid, is_active from orders where sid in (select sid from orders join groups using(gid) where comment::timestamp<NOW()-'%ss'::interval and is_active is true group by sid having sum(loss)>%s) or gid in (select  gid from orders join groups using(gid) where comment::timestamp<NOW()-'%ss'::interval and is_active is true group by gid having sum(loss)>%s) or loss>%s) as foo where is_active is true;" % (ordersTimeout, takeProfit, ordersTimeout, takeProfit, takeProfitSingle))
        for order in self.cur.fetchall():
            orderList.append(order[0])
        return orderList

    def closeOrderFromProfit(self):

        self.cur.execute("select oid from orders where is_active is true and loss between (select sum(loss)/3+(select loss from loss_balance)/2 from orders where is_active is false)*(-1) and %s*(-1) order by gid limit 1" % self.stopLoss)
        fetch = self.cur.fetchone()
        if fetch is not None:
            rows=fetch[0]
        else:
            rows=0
        if rows!=0:
            self.cur.execute("update loss_balance set loss=loss+(select loss from orders where oid=%s)" % rows)
        return rows


###START SCRIPT####
if __name__ == '__main__':

    ########----------CONFIGURATION SECTION----------########
    config = configparser.ConfigParser()
    config.read('config.ini')

    #Pause between making orders
    ordersTimeout=config.getint('orders', 'ordersTimeout')

    #TP & SL
    takeProfit=config.getint('orders', 'takeProfit')
    takeProfitSingle=config.getint('orders', 'takeProfitSingle')
    stopLoss=config.getint('orders', 'stopLoss')
    orderCountLimit=config.getint('orders', 'orderCountLimit')


    #ttl for working script
    scriptTimeout=config.getint('default', 'scriptTimeout')
    symbolSuffix=config.get('default', 'symbolSuffix')


    #database configuration
    db_host=config['database']['dbHost']
    db_port=config['database']['dbPort']
    db_user=config['database']['dbUser']
    db_pass=config['database']['dbPass']
    db_name=config['database']['dbName']

    #list of Symbols
    symbols=config.get('symbols', 'symbolsList')


    ########--------CONFIGURATION SECTION END--------########


    ########-------DATABASE CONNECTION SECTION-------########
    con = psycopg2.connect('host=%s port=%s dbname=%s user=%s password=%s' % (db_host, db_port, db_name, db_user, db_pass))
    con.autocommit = True
    cur = con.cursor()
    ########-----DATABASE CONNECTION SECTION END-----########

    #DWX Connector class init
    _zmq = DWX_ZeroMQ_Connector()

    #signal to prevent endless query to MetaTrader
    signal.signal(signal.SIGALRM, handler)
    0


    '''
    order class has buy and sell orders method.
    we send validPairs from listing symbols in config file. Defaut list of symbols you can find in class __init__
    '''

    ordersObj=order(_zmq, validSymbols=symbols.replace(" ", "").split(','), symbolSuffix=symbolSuffix)

    '''initialize class to work with database'''
    dataToDBObj=dataToDB(cur)

    '''initialize class to analyze orders'''
    analyzeObj=analyze(cur, ordersTimeout, takeProfit, stopLoss, orderCountLimit, takeProfitSingle)


    '''check if all symbols are already in the database'''
    for symbol in ordersObj.returnValidSymbols():
        dataToDBObj.symbolsToDB(symbol)

    i=0
    while True:
        i+=1
        '''
        Here we start signal section, because next part of code used to be stucked sometimes.
        So we use signal with timeout in seconds defined in variable `scriptTimeout`
        '''

        signal.alarm(scriptTimeout)
        0

        #fetching and analizing open trades
        openTradesObj=openTrades(_zmq)


        getAllOpenTrades = 0

        try:
            while getAllOpenTrades==0:
                getAllOpenTrades = openTradesObj.getAllOpenTrades()
        except Exception:
            break

        '''
        Here we end signal section
        '''
        signal.alarm(0)
        0



        '''
        Checking is there are orders in the system. If there are no order -
        we marked variable `makeOrders` as 1, to make orders later in code
        '''

        makeOrders=0


        if getAllOpenTrades:

            for order in getAllOpenTrades:
                dataToDBObj.groupsToDB(getAllOpenTrades[order]['_comment'])
                dataToDBObj.ordersToDB(order=order, symbol=getAllOpenTrades[order]['_symbol'], open_proce=getAllOpenTrades[order]['_open_price'], loss=getAllOpenTrades[order]['_pnl'], group=getAllOpenTrades[order]['_comment'], lots=getAllOpenTrades[order]['_lots'], type=getAllOpenTrades[order]['_type'],   )

        else:

            makeOrders=1



        #########-----ANALYZE SECTION----##########

        '''
        Checking if we are ready to make new orders
        '''

        makeOrders=analyzeObj.oldestOrder()[0]



        #check if group of orders my be closed

        #########---ANALYZE SECTION END--##########


        #########-----ORDERS SECTION-----##########

        '''
        change status for successfully closed orders in orders_pending and orders
        '''
        if len(getAllOpenTrades.keys())>0:
            rowsClosed = dataToDBObj.ordersPendingClosed(tuple(getAllOpenTrades.keys()))
            if rowsClosed!=0:
                print("closedRows")


        '''
        Checking if we are ready to sell orders
        It`s not in analyze section because of conflict between pending and closed orders
        '''

        closeOrders=analyzeObj.closeOrders()

        '''try to close one fuckud-up old order to prevent huge swap'''
        closeOrderFromProfit = analyzeObj.closeOrderFromProfit()
        if closeOrderFromProfit!=0:
            closeOrders.append(closeOrderFromProfit)


        '''if sellOrders list is not empty, let`s sell them'''
        if len(closeOrders)>0:
            print('pending orders')
            for closeorder in closeOrders:

                dataToDBObj.ordersPendingToDB(closeorder)
                ordersObj.closeOrder(closeorder)



        '''
        change status for stucked orders in orders_pending
        '''
        dataToDBObj.ordersPendingFailed()



        '''
        We`ve got 1 on `makeOrders` so, we call use buy method to by all symbols defined in symbols list
        '''

        if makeOrders==1:

            '''
                We make comment with date and time to group orders with.
            '''

            commentDateTime=datetime.now()
            print(commentDateTime)
            for symbol in ordersObj.returnValidSymbols():
                print(symbol)

                ordersObj.openOrder(symbol=symbol, otype=random.randint(0, 1), comment=commentDateTime)


        #########---ORDERS SECTION END---##########



        #########---STATISTICS SECTION---##########

        dataToDBObj.statisticsToDb()

        #########-STATISTICS SECTION END-##########


        print(i)
