
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


def get_PSY(priceData, period=12):
    PSY = pd.DataFrame(
        {
            'date': priceData['date'].reset_index(drop=True),
            'close': priceData['close'].reset_index(drop=True)
        }
    )
    difference = PSY['close'][1:].reset_index(
        drop=True) - PSY['close'][:-1].reset_index(drop=True)
    difference = np.append(0, difference)
    difference_dir = np.where(difference > 0, 1, 0)
    psy_result = np.zeros((len(PSY),))
    psy_result[:period] *= np.nan
    for i in range(period, len(PSY)):
        psy_result[i] = int(
            ((difference_dir[i-period+1:i+1].sum())/period)*100)
    PSY['PSY'] = psy_result
    return PSY


def get_DMI(priceData, period=14):
    DMI = pd.DataFrame(
        {
            'date': priceData['date'][:0:-1],
            'close': priceData['close'][:0:-1],
            'high': priceData['high'][:0:-1],
            'low': priceData['low'][:0:-1]
        }
    )
    # 重設索引 (index)
    DMI = DMI.reset_index(drop=True)
    # 正趨向變動值 +DM = MAX｛Ht - Ht-1，0｝（只取正值，若為負值則設為 0）
    DMI["+DM"] = pd.Series([round(max(DMI['high'][i]-DMI['high'][i+1], 0), 3)
                            for i in range(len(DMI)-1)])
    # 負趨向變動值 -DM = MAX｛Lt-1 - Lt，0｝（只取正值，若為負值則設為 0）
    DMI['-DM'] = pd.Series([round(max(DMI['low'][i+1]-DMI['low'][i], 0), 3)
                            for i in range(len(DMI)-1)])

    # 同一天的 +DM 與 -DM 兩數值相比，較小者設定為 0，兩數若相同則兩數皆設定為 0。
    for i in range(len(DMI)-1):
        if DMI['+DM'][i] - DMI['-DM'][i] > 0:
            DMI.loc[i, '-DM'] = 0.0
        elif DMI['+DM'][i] - DMI['-DM'][i] < 0:
            DMI.loc[i, '+DM'] = 0.0
        else:
            DMI.loc[i, '+DM'] = 0.0
            DMI.loc[i, '-DM'] = 0.0
    # TR = max{∣ Ht - Lt ∣, ∣ Ht - Ct-1 ∣, ∣ Ct-1 - Lt ∣}
    DMI['TR'] = pd.Series([max(abs(DMI['high'][i]-DMI['low'][i]),
                               abs(DMI['high'][i]-DMI['close'][i+1]),
                               abs(DMI['close'][i+1]-DMI['low'][i])) for i in range(len(DMI)-1)])

    # 計算方向指標
    # +ADMt = +ADMt-1 +（+DMt - +ADMt-1）/ n
    # -ADMt = -ADMt-1 +（-DMt - -ADMt-1）/ n
    # ATRt = ATRt-1 +（TRt - ATRt-1）/ n
    # 一般 n 採 14 日為指標的觀察週期
    # 首日 +ADMt = n 日的 +DMt 平均值
    # 首日 -ADMt = n 日的 -DMt 平均值
    # 首日 ATRt = n 日的 TRt 平均值
    # 正方向指標 +DIt = +ADMt / ATRt * 100
    # 負方向指標 -DIt = -ADMt / ATRt * 100
    DMI['+ADM'] = np.zeros((len(DMI),))
    DMI['-ADM'] = np.zeros((len(DMI),))
    DMI['ATR'] = np.zeros((len(DMI),))
    DMI['+DI'] = np.zeros((len(DMI),))
    DMI['-DI'] = np.zeros((len(DMI),))
    DMI['DX'] = np.zeros((len(DMI),))
    DMI['ADX'] = np.zeros((len(DMI),))
    DMI.loc[len(DMI)-1, '+ADM'] = round(sum(DMI['+DM'][:period])/period, 3)
    DMI.loc[len(DMI)-1, '-ADM'] = round(sum(DMI['-DM'][:period])/period, 3)
    DMI.loc[len(DMI)-1, 'ATR'] = round(sum(DMI['TR'][:period])/period, 3)
    for i in range(len(DMI)-2, -1, -1):
        DMI.loc[i, '+ADM'] = DMI['+ADM'][i+1] + \
            (DMI['+DM'][i] - DMI['+ADM'][i+1]) / period
        DMI.loc[i, '-ADM'] = DMI['-ADM'][i+1] + \
            (DMI['-DM'][i] - DMI['-ADM'][i+1]) / period
        DMI.loc[i, 'ATR'] = DMI['ATR'][i+1] + \
            (DMI['TR'][i] - DMI['ATR'][i+1]) / period
    for i in range(len(DMI)):
        DMI.loc[i, '+DI'] = round(DMI['+ADM'][i] / DMI['ATR'][i] * 100, 0)
        DMI.loc[i, '-DI'] = round(DMI['-ADM'][i] / DMI['ATR'][i] * 100, 0)
        DMI.loc[i, 'DX'] = round(
            abs(DMI['+DI'][i] - DMI['-DI'][i]) / (DMI['+DI'][i] + DMI['-DI'][i]) * 100, 0)
    DMI = DMI.loc[::-1]
    DMI = DMI.reset_index(drop=True)
    DMI['ADX'] = round(talib.SMA(DMI['DX'], period), 2)
    return DMI

def buy(day,money,count,tpname,plus,stock):
    if(money  >=  stock['close'][day] * 1000):
        plus = plus + round(stock['close'][day]*1000)
        money = money - round(stock['close'][day]*1000)
        count = count + 1
        #print(tpname," 指標",str(stock.index[day]).split(" ")[0], round(stock[tpname][day], 2), "進行買入","金額",round(stock['close'][day]*1000), "剩餘金額: ", money)
    return money, count, plus

def sell(day,money,count,tpname,avg,stock):
    if(count > 0 and round(stock['close'][day] * 1000) > avg):
        money = money + round(stock['close'][day] * 1000) * count        
        #print(tpname," 指標",str(stock.index[day]).split(" ")[0], round(stock[tpname][day], 2), "進行賣出","張數", count ,"金額",round(stock['close'][day]*1000) * count, "剩餘金額: ", money)
        count = 0
    return money, count

class TechnologyPointer:
    def __init__(self, date='2019-04-12'):
        self.stock = self.get_stock(date)

    # 取 180 天的股市資料
    def get_stock(self, date='2019-04-12'):
        user_select_date_index = int(df.loc[df['date'] == date].index[0])
        return df[user_select_date_index-180:user_select_date_index+1].reset_index(drop=True)

    def get_PSY_profit(self, money=50000):
        cash = TOTAL_ASSETS = money
        buy_record = []
        buy_count = 0
        PSY = get_PSY(self.stock)
        for i in range(12, len(PSY)):
            if PSY['PSY'][i] > 75:
                if buy_count >= 1:
                    if PSY['close'][i] > sum(buy_record) / len(buy_record):
                        buy_count = 0
                        cash += PSY['close'][i] * 1000 * len(buy_record)
                        buy_record.clear()
                        # print(f'{str(PSY["date"][i]).split(" ")[0]} 賣出')
                    else:
                        pass
                        # print(f'{str(PSY["date"][i]).split(" ")[0]} 已達 PSY 賣出標準，但不適合現在賣出')
            elif PSY['PSY'][i] < 25:
                if cash >= PSY['close'][i] * 1000:
                    cash -= PSY['close'][i] * 1000
                    buy_record.append(PSY['close'][i])
                    buy_count += 1
                    # print(f'{str(PSY["date"][i]).split(" ")[0]} 買入')
                elif cash < PSY['close'][i] * 1000:
                    # print('沒錢辣')
                    pass
        
        cash += float(PSY['close'][-1:]) * 1000 * len(buy_record)
        return (cash-TOTAL_ASSETS) / TOTAL_ASSETS
        
    def get_DMI_profit(self, money=50000):
        cash = TOTAL_ASSETS = 50000
        buy_record = []
        buy_count = 0
        DMI = get_DMI(self.stock)
        for i in range(1, len(DMI)-1, 1):
            if DMI['+DI'][i-1] < DMI['-DI'][i-1]:
                if DMI['+DI'][i] >= DMI['-DI'][i]:
                    if DMI['+DI'][i+1] > DMI['-DI'][i+1]:
                        if cash >= DMI['close'][i] * 1000:
                            cash -= DMI['close'][i] * 1000
                            buy_record.append(DMI['close'][i])
                            buy_count += 1
                            # print(f'{str(DMI["date"][i]).split(" ")[0]} 買入')
                        elif cash < DMI['close'][i] * 1000:
                            pass
                            # print('沒錢辣')
            elif DMI['+DI'][i-1] > DMI['-DI'][i-1]:
                if DMI['+DI'][i] <= DMI['-DI'][i]:
                    if DMI['+DI'][i+1] < DMI['-DI'][i+1]:
                        if buy_count > 1:
                            if DMI['close'][i] > sum(buy_record) / len(buy_record):
                                buy_count = 0
                                cash += DMI['close'][i] * 1000 * len(buy_record)
                                buy_record.clear()
                                # print(f'{str(DMI["date"][i]).split(" ")[0]} 賣出')
                            else:
                                pass
                                # print(f'{str(DMI["date"][i]).split(" ")[0]} 已達 DMI 賣出標準，但不適合現在賣出')
        if buy_count > 0:
            cash += float(DMI['close'][-1:]) * 1000 * len(buy_record)
            return (cash-TOTAL_ASSETS) / TOTAL_ASSETS

    def get_OBV_profit(self,money=50000):
        count = 0
        plus = 0
        for i in range(len(self.stock["OBV"])):
            if (self.stock["OBV"][i] < 0) and (self.stock["OBV"][i - 1] > 0):
                money,count,plus = buy(i,money,count,"OBV", plus)                     
            elif (self.stock["OBV"][i] > 0) and (self.stock["OBV"][i - 1] < 0):  
                if(count > 0):
                    money,count = sell(i,money,count,"OBV", plus/count, self.stock)
                else:
                    money,count = sell(i,money,count,"OBV", plus, self.stock)
        return (money + round(self.stock["close"][-1]) * count * 1000) / 50000
    
    def get_AR_profit(self,money=50000):
        count = 0
        plus = 0
        for i in range(len(self.stock["AR"])):
            if (self.stock["AR"][i] < 0.5):
                money,count,plus = buy(i,money,count,"AR",plus, self.stock)                
            elif (self.stock["AR"][i] > 1.5):
                if(count > 0):
                    money,count = sell(i,money,count,"AR",plus/count, self.stock)
                else:
                    money,count = sell(i,money,count,"AR",plus) 
        return (money + round(self.stock["close"][-1]) * count * 1000) / 50000
    
    def get_BR_profit(self,money=50000):
        count = 0
        plus = 0
        for i in range(len(self.stock["BR"])):
            if (self.stock["BR"][i] * 100 < 80) and (self.stock["AR"][i] * 100 < 50):           
                money,count,plus = buy(i,money,count,"BR",plus)
            elif (self.stock["BR"][i] * 100 > 250) and (self.stock["AR"][i] * 100 > 150):
                if(count > 0):
                    money,count = sell(i,money,count,"BR",plus/count)
                else:
                    money,count = sell(i,money,count,"BR",plus)
        return (money + round(self.stock["close"][-1]) * count * 1000) / 50000

    ##print("OBV獲利率:", (money + round(df["close"][-1]) * count * 1000) / 50000)
