
import sqlite3
import numpy as np
import pandas as pd
import talib

data_base = sqlite3.connect('./db.sqlite3')
# SQL operation
df = pd.read_sql('select 日期, 證券代號, 開盤價, 收盤價, 最高價, 最低價, 成交股數 from daily_price where 證券代號="2302"',
                data_base,
                # 依照日期排
                # index_col=['日期'],
                parse_dates=['日期'])
# close data base connect
data_base.close()
# rename the columns of dataframe
df.rename(columns={'收盤價': 'close', '開盤價': 'open', '最高價': 'high', '日期': 'date',
                '最低價': 'low', '成交股數': 'volume'}, inplace=True)
# sort by date
df = df.sort_values(by='date')

class TechnologyPointer:
    def __init__(self, date='2019-04-12'):
        self.stock = self.get_stock(date)

    def get_stock(self, date='2019-04-12'):
        user_select_date_index = int(df.loc[df['date'] == date].index[0])
        return df[user_select_date_index-180:user_select_date_index+1].reset_index(drop=True)

    def get_KD_profit(self, capital = 50000):

        funds = capital
        #股票張數
        thousand_shares = 0
        #買入點的價錢
        closing_price_buy = []

        #KD鈍化變數
        KAbove80 = 0
        KUnder20 = 0
        KAbove80ThreeDays = False
        KUnder20ThreeDays = False

        #當天KD狀態
        KBiggerThanDToday = False

        #前一天KD狀態
        KBiggerThanDOneDayBefore = False
        # if 第一天的 K > D:
        #     KBiggerThanDOneDayBefore = True

        k,d = talib.STOCH(self.stock['high'],self.stock['low'],self.stock['close'])
    
        for date,close,K,D in zip(self.stock['date'],self.stock['close'],k,d):
        
            #判斷KD鈍化
            if K > 80 :
                KAbove80 += 1
            elif K < 20 :
                KUnder20 += 1
            else:
                KAbove80 = 0
                KUnder20 = 0
            
            if KAbove80 >= 3:
                KAbove80ThreeDays = True
            else:
                KAbove80ThreeDays = False
            
            if KUnder20 >= 3:
                KUnder20ThreeDays = True
            else:
                KUnder20ThreeDays = False
        
            if K > D:
                KBiggerThanDToday = True
            else:
                KBiggerThanDToday = False
            
            #1張股票的價錢
            thousand_shares_price = close * 1000

            #黃金交叉，買入
            if KBiggerThanDToday and not(KBiggerThanDOneDayBefore) and not(KAbove80ThreeDays) and not(KUnder20ThreeDays):
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(close)
                    print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'KD黃金交叉 買入')
            elif KUnder20ThreeDays :
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(close)
                    print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'K<20 3天了 買入')
            #死亡交叉，賣出
            elif not(KBiggerThanDToday) and KBiggerThanDOneDayBefore and not(KAbove80ThreeDays) and not(KUnder20ThreeDays) and len(closing_price_buy) > 0:
                if close > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'KD死亡交叉 賣出')
            elif KAbove80ThreeDays and len(closing_price_buy) > 0:
                if close > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'K>80 3天了 賣出')
            # #其他資訊
            # else:
            #     print(date, ',close =', close, ',K =', round(K,2), ',D =', round(D,2), ',KD info',end = ' ')
            #     print(',K > 80幾天',KAbove80,',K > 80 3天', KAbove80ThreeDays,',K<20幾天',KUnder20,',K<20 3天',KUnder20ThreeDays,',K>D',KBiggerThanDToday,',昨天K>D',KBiggerThanDOneDayBefore)
            
            KBiggerThanDOneDayBefore = KBiggerThanDToday
    
        return (funds + thousand_shares * thousand_shares_price - capital)/capital

    def get_RSI_profit(self, capital = 50000):

        funds = capital
        #股票張數
        thousand_shares = 0
        #買入點的價錢
        closing_price_buy = []
        #交叉變數
        RSIShort_under_RSILong_today = False
        RSIShort_under_RSILong_yesterday = False
        
        #短周期6天 長周期14天
        self.stock["RSI6"] = talib.RSI(self.stock['close'], timeperiod = 6)
        self.stock["RSI14"] = talib.RSI(self.stock['close'], timeperiod = 14)

        for date,closing_price,RSIShort,RSILong in zip(self.stock['date'],self.stock['close'],self.stock['RSI6'],self.stock['RSI14']):
        
            if RSIShort < RSILong:
                RSIShort_under_RSILong_today = True
            else:
                RSIShort_under_RSILong_today = False

            #1張股票的價錢
            thousand_shares_price = closing_price * 1000

            #RSI<20，買入信號
            if RSIShort < 20 or RSILong < 20:
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI6 OR RSI14 < 20 買入')
            #RSI黃金交叉，買入信號
            elif not(RSIShort_under_RSILong_today) and RSIShort_under_RSILong_yesterday:
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI黃金交叉 買入')
            #RSI>80，賣出信號
            elif (RSIShort > 80 or RSILong > 80) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI6 OR RSI14 > 80 賣出')
            #RSI死亡交叉，賣出信號
            elif RSIShort_under_RSILong_today and not(RSIShort_under_RSILong_yesterday) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI死亡交叉 賣出')

            RSIShort_under_RSILong_yesterday = RSIShort_under_RSILong_today
        return (funds + thousand_shares * thousand_shares_price - capital)/capital

    def get_MA_profit(self, capital = 50000):

        funds = capital
        #股票張數
        thousand_shares = 0
        #買入點的價錢
        closing_price_buy = []

        closing_price_above_MA_yesterday = False
        closing_price_yesterday = 0
        sma_yesterday = 0
        closing_price_slope_yesterday = 0

        SMA = talib.SMA(self.stock['close'],6)

        for date,closing_price,sma in zip(self.stock['date'],self.stock['close'],SMA):
            
            #乖離率
            BIAS = (closing_price - sma) / sma

            #斜率(趨勢用)
            closing_price_slope = (closing_price - closing_price_yesterday) / 1
            sma_slope = (sma - sma_yesterday) / 1
            # print(sma_slope)
            #今天收盤價在移動平均線上面
            if closing_price > sma:
                closing_price_above_MA_today = True
            else:
                closing_price_above_MA_today = False
            
            #1張股票的價錢
            thousand_shares_price = closing_price * 1000

            #A點:收盤價突破移動平均線(所以要看前一天收盤價是否在MA以下)，買入訊號
            if not(closing_price_above_MA_yesterday) and closing_price_above_MA_today:
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',A點買入')
            # #B點:乖離不大，趨勢發展，預期乖離變大，為買入訊號。(沒跌破均線)
            # elif BIAS < 0.3 and closing_price_above_MA_today and closing_price_slope > 0 :
            #     if funds >= thousand_shares_price :
            #         funds = funds - thousand_shares_price
            #         thousand_shares += 1
            #         closing_price_buy.append(closing_price)
            #         print(date, ',close =', closing_price, ',MA =', round(sma,2), ',B點買入')
            #C點:MA持續上升，股價急跌，跌破均線後的反彈點，且均線仍在上升，此為急跌後反彈的買進訊號
            elif sma_slope > 0 and closing_price_slope_yesterday < 0 and not(closing_price_above_MA_today) and closing_price_slope > 0:
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',C點買入')
            #D點:價格自高點跌破均線，且跌深，價格偏離均線很多(假設值)，可能修正，為買進訊號
            elif sma - closing_price < 3 and closing_price_slope_yesterday < 0 and closing_price_slope > 0:
                if funds >= thousand_shares_price :
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',D點買入')
            #E點:處上漲階段，價格短期漲幅過大(假設值)，導致與平均線偏離太多(假設值)，預期短期會有獲利賣壓，價格會有修正，為賣出訊號
            elif closing_price_slope > 0.5 and closing_price - sma > 3 and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',E點賣出')
            #F點:趨勢往下跑且股價從上跌破MA，趨勢反轉、死亡交叉，為賣出訊號
            elif closing_price_above_MA_yesterday and not(closing_price_above_MA_today) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',F點賣出')
            # #G點:乖離不大(假設值)，趨勢加速發展(可能要設閥值)，預期乖離擴大，價格下跌速度快，且股價沒有突破MA，為賣出訊號
            # elif BIAS < 0.3 and closing_price_slope > 0 and not(closing_price_above_MA_today and len(closing_price_buy) > 0):
                # if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                #     funds = funds + thousand_shares * thousand_shares_price
                #     thousand_shares = 0
                #     closing_price_buy = []
                #     print(date, ',close =', closing_price, ',MA =', round(sma,2), ',G點賣出')
            #H點:股價突破MA後迅速拉回，為假突破訊號，表示趨勢持續，此時MA仍然向下，為賣出訊號
            elif closing_price_above_MA_yesterday and not(closing_price_above_MA_today) and sma_slope < 0 and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    print(date, ',close =', closing_price, ',MA =', round(sma,2), ',H點賣出')

            #紀錄前一天的狀態
            closing_price_above_MA_yesterday = closing_price_above_MA_today
            sma_yesterday = sma
            closing_price_slope_yesterday = (closing_price - closing_price_yesterday) / 1
        return (funds + thousand_shares * thousand_shares_price - capital)/capital

    def get_xxx_profit(self, money=50000):
        
        print(get_stock().head(10))
        return # 獲利率
