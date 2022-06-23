import requests
from bs4 import BeautifulSoup

class tradingPairs():
    def __init__(self, 
    _allTypePairs = {
        'minor': { 
            'url': 'https://www.tradingview.com/markets/currencies/rates-minor/', 
            'availiablePairs' : ('AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'NZDJPY')
            },
        'major': {
            'url': 'https://www.tradingview.com/markets/currencies/rates-major/', 
            'availiablePairs' : ('AUDUSD', 'EURUSD', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY')
            },
        'metal': {
            'url': 'https://www.tradingview.com/markets/futures/quotes-metals/', 
            'availiablePairs' : ('QI1!', 'GC1!')
            }      
        },
        _dataSymbol=('FX_IDC', 'COMEX', 'COMEX_MINI')
    ):

        self.allTypePairs=_allTypePairs
        self.dataSymbol=_dataSymbol

    def getPairs(self):
        returnList=[]
        for typePair in self.allTypePairs:
            url = self.allTypePairs[typePair]['url']
            availiablePairs = self.allTypePairs[typePair]['availiablePairs']
            page = requests.get(url)
            soup = BeautifulSoup(page.text, 'html.parser')
            for pair in availiablePairs:
                for dSID in self.dataSymbol:
                    try:
                        
                        pairString = soup.find("tr", attrs={'data-symbol': '%s:%s' % (dSID, pair)})
                        
                        pairStringSignal = pairString.find('span', class_='tv-screener-table__signal')
                        returnList.append(pair.lower().replace('qi1!', 'xagusd').replace('gc1!', 'xauusd')+"-"+pairStringSignal.text.lower().replace('strong ', ''))
                        #print(pair.lower() , "-", pairStringSignal.text.lower(), sep='')
                    except:
                        pass
        
        return returnList

