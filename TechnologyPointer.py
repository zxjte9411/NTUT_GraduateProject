
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

    def get_xxx_profit(self, money=50000):
        
        print(get_stock().head(10))
        return # 獲利率
        
funds = TechnologyPointer().get_KD_profit()
print(funds)