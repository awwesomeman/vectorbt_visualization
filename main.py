
from plot import Plot

class My_Strategy(Plot):

    def __init__(self,api):
         super().__init__(api)

    def KDJMA(self, time_period = 10,oversell = 20,overbuy = 80, ma1 = 5,ma2 = 20,trading_type='standard'):

        #-------------------------------------------------
        # calculate k, d , j
        #-------------------------------------------------
        data = self.kbars_df
        ini_k = 50
        ini_d = 50
        k=[]
        d=[]
        rsv = (data['Close'].rolling(time_period).apply(lambda x:x[-1]) - data["Low"].rolling(time_period).min() ) / ( data["High"].rolling(time_period).max() - data["Low"].rolling(time_period).min() ) *100
        rsv = rsv.dropna()
        
        for _ in rsv:
            ini_k =  2/3 * ini_k + 1/3 * _
            k.append(ini_k)

        for _ in k:
            ini_d =  2/3 * ini_d + 1/3 * _
            d.append(ini_d)  
        k = pd.Series(k,index = rsv.index)
        d = pd.Series(d,index = rsv.index)
        j = 3 * k - 2 * d
        ma1 = data['Close'].rolling(ma1).mean()
        ma2 = data['Close'].rolling(ma2).mean()
        #-------------------------------------------------
        # make strategy signals
        #-------------------------------------------------
        
        init_buy_sig = ( j>oversell ) & ( j.shift()<oversell ) & (ma1>ma2)
        init_sell_sig = ( j<overbuy ) & ( j.shift()>overbuy ) & (ma1<ma2)
        indicators = [('sub',{"K":k,"D":d,"J":j}),('main',{"ma1":ma1,"ma2":ma2})]  # [('sub', {indicators1}), ('main'{indicators2})......]
        
        self.init_buy_sig = init_buy_sig
        self.init_sell_sig = init_sell_sig            
        self.indicators = indicators
        self.trading_type = trading_type  
    
    def MA(self, ma1 = 5,ma2 = 20,trading_type='standard'):

        #-------------------------------------------------
        # calculate ma
        #-------------------------------------------------
        data = self.kbars_df
        ma1 = data['Close'].rolling(ma1).mean()
        ma2 = data['Close'].rolling(ma2).mean()

        #-------------------------------------------------
        # make strategy signals
        #-------------------------------------------------
        
        init_buy_sig = ( ma1>ma2 ) & ( ma1.shift()<ma2 )
        init_sell_sig = ( ma1<ma2 ) & ( ma1.shift()>ma2 )
        indicators = [('main',{"ma1":ma1,"ma2":ma2})]  # [('sub', {indicators1}), ('main'{indicators2})......]
        
        self.init_buy_sig = init_buy_sig
        self.init_sell_sig = init_sell_sig            
        self.indicators = indicators
        self.trading_type = trading_type

    def KDJ(self, time_period = 10,oversell = 20,overbuy = 80,trading_type='standard'):

        #-------------------------------------------------
        # calculate k, d , j
        #-------------------------------------------------
        data = self.kbars_df
        ini_k = 50
        ini_d = 50
        k=[]
        d=[]
        rsv = (data['Close'].rolling(time_period).apply(lambda x:x[-1]) - data["Low"].rolling(time_period).min() ) / ( data["High"].rolling(time_period).max() - data["Low"].rolling(time_period).min() ) *100
        rsv = rsv.dropna()
        
        for _ in rsv:
            ini_k =  2/3 * ini_k + 1/3 * _
            k.append(ini_k)

        for _ in k:
            ini_d =  2/3 * ini_d + 1/3 * _
            d.append(ini_d)  
        k = pd.Series(k,index = rsv.index)
        d = pd.Series(d,index = rsv.index)
        j = 3 * k - 2 * d
        
        #-------------------------------------------------
        # make strategy signals
        #-------------------------------------------------
        
        init_buy_sig = ( j>oversell ) & ( j.shift()<oversell )
        init_sell_sig = ( j<overbuy ) & ( j.shift()>overbuy )

        # 模擬真實交易狀況，在訊號出現的下一個交易機會買入
        init_buy_sig = init_buy_sig.shift().dropna()
        init_sell_sig = init_sell_sig.shift().dropna()

        indicators = [('sub',{"K":k,"D":d,"J":j})]  # [('sub', {indicators1}), ('main'{indicators2})......]
        
        self.init_buy_sig = init_buy_sig
        self.init_sell_sig = init_sell_sig            
        self.indicators = indicators
        self.trading_type = trading_type
        

