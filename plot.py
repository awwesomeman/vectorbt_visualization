import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import shioaji as sj
from tabulate import tabulate
import yfinance as yf
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore")

api = sj.Shioaji()
api.login("id_num", "password")
api.activate_ca(
ca_path="C:\\Users\\tsunglin\\Desktop\\SinoPac.pfx",
ca_passwd="id_num",
person_id="id_num")

class Plot():
    def __init__(self,api=api):
        self.api = api

    def input_stock(self,kbars_df,stock_id,freq='B'):
        
        if freq =='M':
            label = 'left'
        else:
            label = 'right'

        data = {
        "Open":kbars_df["Open"].resample(freq,closed='right',label=label).first(),
        "High":kbars_df["High"].resample(freq,closed='right',label=label).max(),
        "Low":kbars_df["Low"].resample(freq,closed='right',label=label).min(),
        "Close":kbars_df["Close"].resample(freq,closed='right',label=label).last(),
        "Volume":kbars_df["Volume"].resample(freq,closed='right',label=label).sum()
        }
        kbars_df = pd.DataFrame(data,index=data['Open'].index).dropna()
        self.freq = freq
        self.stock_id = stock_id
        self.kbars_df = kbars_df
        
    def get_stock(self,stock_id,start,end,freq='B'):
        '''
            freq = Day -> 'B', 
            Minutes -> '10T', 
            Week -> 'W',
            Month -> 'M', set label = 'left'
        '''

        if freq =='M':
            label = 'left'
        else:
            label = 'right'

        contract = self.api.Contracts.Stocks[stock_id]
        kbars = self.api.kbars(contract, start=start, end=end)
        kbars_df = pd.DataFrame({**kbars})
        kbars_df.ts = pd.to_datetime(kbars_df.ts)
        kbars_df = kbars_df.set_index('ts')
        data = {
        "Open":kbars_df["Open"].resample(freq,closed='right',label=label).first(),
        "High":kbars_df["High"].resample(freq,closed='right',label=label).max(),
        "Low":kbars_df["Low"].resample(freq,closed='right',label=label).min(),
        "Close":kbars_df["Close"].resample(freq,closed='right',label=label).last(),
        "Volume":kbars_df["Volume"].resample(freq,closed='right',label=label).sum()
        }
        kbars_df = pd.DataFrame(data,index=data['Open'].index).dropna()
        kbars_df.index.name="Date"

        self.freq = freq
        self.stock_id = stock_id
        self.kbars_df = kbars_df

    def __strategy_type(self):
        data = self.kbars_df
        trading_type =  self.trading_type
        init_buy_sig = self.init_buy_sig
        init_sell_sig = self.init_sell_sig

        if trading_type == 'standard':
            
            buy_sig=init_buy_sig.copy()
            buy_sig[init_buy_sig]=1
            buy_sig[init_sell_sig]=-1
            strategy_sig = buy_sig.replace(0,np.nan).ffill()

            strategy_buy = strategy_sig[strategy_sig.diff()==2]
            strategy_sell = strategy_sig[strategy_sig.diff()==-2]

            strategy_buy_mark = data[data.index.isin(strategy_buy.index)]
            strategy_buy_mark['Signal'] = 1
            strategy_sell_mark = data[data.index.isin(strategy_sell.index)]
            strategy_sell_mark['Signal'] = 0

        if trading_type =='customize':
            pass
        
        return strategy_sell_mark, strategy_buy_mark

    def run(self,enter_comm=0.001425*0.28,exit_comm=0.001425*0.28+0.003,buy_at_kbar="Close", sell_at_kbar="Close"):
        
        sell_mark, buy_mark = self.__strategy_type()
        self.buy_mark = buy_mark
        self.sell_mark = sell_mark
        self.buy_at_kbar = buy_at_kbar
        self.sell_at_kbar = sell_at_kbar
        
        df = pd.concat([buy_mark, sell_mark],join='outer',sort=False).sort_index()
        df['Holding periods'] = df.index.to_series().diff().shift(-1)
        df['Profit'] = (df[sell_at_kbar].shift(-1)*(1-exit_comm) - df[buy_at_kbar]*(1+enter_comm)) / (df[buy_at_kbar]*(1+enter_comm))
        df['Absolute value'] = df['Profit'].abs()
        df['Gain / Loss'] = df['Profit']>0
        df['Gain / Loss'] = df['Gain / Loss'].map({True:'$Gain$',False:'Loss'})
        
        profit = df[df['Signal'] == 1][['Profit','Holding periods','Absolute value','Gain / Loss']]
        profit = profit.dropna()
        profit['Cumulative ret'] = (profit['Profit']+1).cumprod()
        profit['Maximum draw drown'] = ((profit['Cumulative ret'] - profit['Cumulative ret'].cummax())/profit['Cumulative ret'].cummax())


        average = (profit['Profit'].mean()) * 100
        std = profit['Profit'].std()
        win_rate = ((profit['Profit']>0).sum() / len(profit))*100
        average_period = profit['Holding periods'].mean()
        num_trade =  len(profit)
        data = {"Average return(%)":average,"Strategy std":std,"Number of trades":num_trade,"Winning rate(%)":win_rate,'Average holding periods':average_period}
        strategy_info = pd.DataFrame(data,index=['Strategy info'])

        profit[['Profit','Absolute value','Cumulative ret','Maximum draw drown']] = (profit[['Profit','Absolute value','Cumulative ret','Maximum draw drown']]).apply(lambda x:round(x,4))
        strategy_info[['Average return(%)','Strategy std','Winning rate(%)']] = (strategy_info[['Average return(%)','Strategy std','Winning rate(%)']]).apply(lambda x:round(x,4))
        print(tabulate(profit,headers=profit.columns, tablefmt='pretty'))
        print(tabulate(strategy_info,headers=strategy_info.columns, tablefmt='pretty'))
        
        self.trading_detail = df
        self.profit_detail = profit
        self.strategy_info = strategy_info
        
    def plot(self):

        df = self.kbars_df
        freq = self.freq   
        stock_id = self.stock_id     
        indicator_set = self.indicators
        buy_mark = self.buy_mark
        sell_mark = self.sell_mark
        profit_detail = self.profit_detail
        buy_at_kbar = self.buy_at_kbar 
        sell_at_kbar = self.buy_at_kbar
        #----------------------------------------------------------------------------------
        # create plot
        #----------------------------------------------------------------------------------
        # candle stick, buy and sell signals (y6)
        #----------------------------------------------------------------------------------
        fig = go.Figure()
        
        fig.add_trace(
            go.Candlestick(x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df ['Close'],
                    name="Stock Prices",
                    increasing={'line': {'color': '#DC3912'}},
                    decreasing={'line': {'color': '#222A2A'}},
                    yaxis='y6' ))

        fig.add_trace(
                go.Scatter(
                    x=buy_mark.index,
                    y=buy_mark[buy_at_kbar], 
                    name="Buy Signal",
                    marker=dict(color="#0DF9FF", size=15),
                    mode="markers",
                    marker_symbol="triangle-up",
                    yaxis='y6'))

        fig.add_trace(
                go.Scatter(
                    x=sell_mark.index,
                    y=sell_mark[sell_at_kbar], 
                    name="Sell Signal",
                    marker=dict(color="#778AAE", size=15),
                    mode="markers",
                    marker_symbol="triangle-down",
                    yaxis='y6'))
        #----------------------------------------------------------------------------------
        # technical indicator (y5 or y6)
        #----------------------------------------------------------------------------------
        
        if indicator_set:
            for indicators in indicator_set:
                
                if indicators[0]=="main":
                    
                    for indicator_name, indicator in indicators[1].items():
                        fig.add_trace(
                                go.Scatter(
                                    x=indicator.index,
                                    y=indicator,
                                    name=indicator_name,
                                    yaxis='y6'))

                if indicators[0]=="sub":
                    
                    for indicator_name, indicator in indicators[1].items():
                        fig.add_trace(
                                go.Scatter(
                                    x=indicator.index,
                                    y=indicator,
                                    name=indicator_name,
                                    yaxis='y5'))

        #----------------------------------------------------------------------------------
        # volume (y4)
        #----------------------------------------------------------------------------------
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                yaxis='y4',
                name='Volume',
                marker_color='#795548'))  

        #----------------------------------------------------------------------------------
        # individual profit plot (y3)
        #----------------------------------------------------------------------------------



        fig.add_trace(
            go.Scatter( 
            x=profit_detail.index, 
            y=profit_detail.Profit*100, 
            marker_size = (profit_detail["Absolute value"])*100,
            marker_color = profit_detail["Gain / Loss"].map({'$Gain$':'#D62728',"Loss":'#2CA02C'}),

            marker_symbol='circle',
            mode='markers',
            yaxis='y3',
            name = 'Gain/Loss for each trade(%)'))



        #----------------------------------------------------------------------------------
        # cumulative profit plot (y2)
        #----------------------------------------------------------------------------------
        fig.add_trace(
                go.Scatter(
                    x=profit_detail.index,
                    y=profit_detail['Cumulative ret']*100,
                    name='Cumulative return(%)',
                    line_color='#3366CC',
                    yaxis='y2'))
        #----------------------------------------------------------------------------------
        # maximum drawdown (y)
        #----------------------------------------------------------------------------------

        fig.add_trace(
                go.Scatter(
                    x=profit_detail.index,
                    y=profit_detail['Maximum draw drown']*100,
                    name='Maximum draw down(%)',
                    line_color='#DC3912',
                    yaxis='y'))


        #----------------------------------------------------------------------------------
        # setup layout
        #----------------------------------------------------------------------------------
        # y axis
        #----------------------------------------------------------------------------------
        fig.update_layout(
            xaxis=dict(
                autorange=True,
                rangeslider=dict(
                    autorange=True,
                    ),
                type="date"
            ),
            yaxis=dict(
                anchor="x",
                autorange=True,
                domain=[0, 0.1],
                linecolor="#DC3912",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#DC3912"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#DC3912"},
                type="linear",
                zeroline=False,
            ),

            yaxis2=dict(
                anchor="x",
                autorange=True,
                domain=[0.11, 0.2],
                linecolor="#3366CC",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#3366CC"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#3366CC"},
                type="linear",
                zeroline=False,
            ),

            yaxis3=dict(
                anchor="x",
                autorange=True,
                domain=[0.21, 0.35],
                linecolor="#222A2A",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#222A2A"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#222A2A"},
                type="linear",
                zeroline=True,
            ),
                
            yaxis4=dict(
                anchor="x",
                autorange=True,
                domain=[0.36, 0.45],
                linecolor="#795548",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#795548"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#795548"},
                type="linear",
                zeroline=False,
                
            ),


            yaxis5=dict(
                anchor="x",
                autorange=True,
                domain=[0.46, 0.55],
                linecolor="#673ab7",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#673ab7"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#673ab7"},
                type="linear",
                zeroline=False,
                
            ),



            yaxis6=dict(
                anchor="x",
                autorange=True,
                domain=[0.56, 1],
                linecolor="#E91E63",
                mirror=True,
                showline=True,
                side="right",
                tickfont={"color": "#E91E63"},
                tickmode="auto",
                ticks="",
                titlefont={"color": "#E91E63"},
                type="linear",
                zeroline=False,
                
            ))

        #----------------------------------------------------------------------------------
        # final settings
        #----------------------------------------------------------------------------------
        
        fig.update_traces(decreasing_line_width=2,increasing_line_width=2,whiskerwidth=0.5, selector=dict(type='candlestick'))

        if freq=='B':
            fig.update_xaxes(rangebreaks=[
                    dict(bounds=['sat', 'mon'])])  

        if freq[-1]=='T':   
            fig.update_xaxes(rangebreaks=[dict(bounds=[14, 9], pattern="hour"),
                              dict(bounds=['sat', 'mon'])])
        


        fig.update_layout(
            title = f'STOCK ID : {stock_id}, Data frequency:{freq}',
            dragmode="zoom",
            hovermode="x",
            legend=dict(orientation="h",
                yanchor="top",
                xanchor="center",
                y=-0.3,
                x=0.5,
                traceorder="reversed"),
            height=1000,
            width=1000,
            template="plotly_white",
            margin=dict(
                l = 70,
                r = 70,
                t=100,
                b=50
            ),
        )

        fig.show()