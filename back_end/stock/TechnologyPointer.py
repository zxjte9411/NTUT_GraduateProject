import sqlite3
import os
import uuid

import numpy as np
import pandas as pd
import talib
from talib import abstract
from matplotlib import pyplot as plt
from matplotlib.pylab import date2num
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_RANGE = 390
plt.rcParams["figure.figsize"] = (8, 5)
DB_NAME = 'db.sqlite3'
data_base = sqlite3.connect(f'{BASE_PATH}/{DB_NAME}')
stock_nums = pd.read_sql(
    'select DISTINCT 證券代號 from daily_price ORDER BY 證券代號', data_base)['證券代號'].values
DEFAULT_STOCK_LAST_DATE = pd.read_sql(
    'select DISTINCT 日期 from daily_price ORDER BY 日期 DESC limit 0, 1', data_base)['日期'].values[0].split(' ')[0]

# close data base connect
data_base.close()

plt.rcParams["figure.figsize"] = (8, 5)


def get_OBV(priceData):
    OBV = pd.DataFrame(
        {
            'close': priceData['close'].reset_index(drop=True),
            'volume': priceData['volume'].reset_index(drop=True)
        }
    )
    OBV['OBV'] = talib.OBV(OBV['close'], OBV['volume'])
    return OBV


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
    return PSY['PSY']


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
    plusDM = []
    negativeDM = []
    TR = []
    for i in range(len(DMI)-1):
        # 正趨向變動值 +DM = MAX｛Ht - Ht-1，0｝（只取正值，若為負值則設為 0）
        plusDM.append(round(max(DMI['high'][i]-DMI['high'][i+1], 0), 3))
        # 負趨向變動值 -DM = MAX｛Lt-1 - Lt，0｝（只取正值，若為負值則設為 0）
        negativeDM.append(round(max(DMI['low'][i+1]-DMI['low'][i], 0), 3))
        # TR = max{∣ Ht - Lt ∣, ∣ Ht - Ct-1 ∣, ∣ Ct-1 - Lt ∣}
        TR.append(max(abs(DMI['high'][i]-DMI['low'][i]),
                      abs(DMI['high'][i]-DMI['close'][i+1]),
                      abs(DMI['close'][i+1]-DMI['low'][i])))
        # 同一天的 +DM 與 -DM 兩數值相比，較小者設定為 0，兩數若相同則兩數皆設定為 0。
        if plusDM[i] - negativeDM[i] > 0:
            negativeDM[i] = 0.0
        elif plusDM[i] - negativeDM[i] < 0:
            plusDM[i] = 0.0
        else:
            plusDM[i] = 0.0
            negativeDM[i] = 0.0
    DMI["+DM"] = pd.Series(plusDM)
    DMI['-DM'] = pd.Series(negativeDM)
    DMI['TR'] = pd.Series(TR)

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
    # DMI['DX'] = np.zeros((len(DMI),))
    # DMI['ADX'] = np.zeros((len(DMI),))
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
        DMI.loc[i, '+DI'] = round(DMI['+ADM'][i] / DMI['ATR'][i] * 100, 0)
        DMI.loc[i, '-DI'] = round(DMI['-ADM'][i] / DMI['ATR'][i] * 100, 0)
    # for i in range(len(DMI)):
        # DMI.loc[i, 'DX'] = round(abs(DMI['+DI'][i] - DMI['-DI'][i]) / (DMI['+DI'][i] + DMI['-DI'][i]) * 100, 0)
    DMI = DMI.loc[::-1]
    DMI = DMI.reset_index(drop=True)
    # DMI['ADX'] = round(talib.SMA(DMI['DX'], period), 2)
    return DMI


def buy(day, money, count, plus, stock):
    plus = plus + round(stock['close'][day]*1000)
    money = money - round(stock['close'][day]*1000)
    count = count + 1

    return money, count, plus


def sell(day, money, count, stock):
    money = money + round(stock['close'][day] * 1000) * count
    count = 0
    return money, count, 0


def check_img_file_amount_and_delete():
    list_dirs = os.listdir(f'{BASE_PATH}/static/stock/img/line_graph/')
    if len(list_dirs) + 1 > 10:
        for i in list_dirs:
            os.remove(f'{BASE_PATH}/static/stock/img/line_graph/{i}')


class TechnologyPointer:
    def __init__(self, date=DEFAULT_STOCK_LAST_DATE, stock_number='2302'):
        data_base = sqlite3.connect(f'{BASE_PATH}/{DB_NAME}')
        self.stock_number = stock_number
        self.df = pd.read_sql(f'select 日期, 證券代號, 開盤價, 收盤價, 最高價, 最低價, 成交股數 from daily_price where 證券代號="{stock_number}"',
                              data_base, parse_dates=['日期'])
        self.df.rename(columns={'收盤價': 'close', '開盤價': 'open', '最高價': 'high', '日期': 'date',
                                '最低價': 'low', '成交股數': 'volume'}, inplace=True)
        self.df.sort_values(by='date')
        data_base.close()
        self.stock = self.get_stock(date)
        self.PSY_detail = []
        self.DMI_detail = []
        self.OBV_detail = []
        self.RSI_detail = []
        self.AR_detail = []
        self.BR_detail = []
        self.KD_detail = []
        self.MA_detail = []
        # {
        #    'date': '2019-08-08',
        #    'close' : '5'
        #    'type' : 買\賣
        # }

    # 取 x 天的股市資料
    def get_stock(self, date=DEFAULT_STOCK_LAST_DATE):
        user_select_date_index = int(
            self.df.loc[self.df['date'] == date].index[0])
        stock = self.df[user_select_date_index -
                        DATA_RANGE:user_select_date_index+1].reset_index(drop=True)

        stock["AR"] = talib.SUM(self.df.high - self.df.open, timeperiod=26) / \
            talib.SUM(self.df.open - self.df.low, timeperiod=26)*100
        stock["BR"] = talib.SUM(self.df.high - self.df.close.shift(1), timeperiod=26) / \
            talib.SUM(self.df.close.shift(1) - self.df.low, timeperiod=26)*100
        stock['PSY'] = get_PSY(stock)
        stock['K'], stock['D'] = talib.STOCH(
            stock['high'], stock['low'], stock['close'])
        # 短周期6天 長周期14天
        stock['RSI6'] = talib.RSI(stock['close'], timeperiod=6)
        stock['RSI14'] = talib.RSI(stock['close'], timeperiod=14)
        stock['SMA'] = talib.SMA(stock['close'], 6)
        stock["AR"] = talib.SUM(self.df.high - self.df.open, timeperiod=26) / \
            talib.SUM(self.df.open - self.df.low, timeperiod=26)*100
        stock["BR"] = talib.SUM(self.df.high - self.df.close.shift(1), timeperiod=26) / \
            talib.SUM(self.df.close.shift(1) - self.df.low, timeperiod=26)*100

        return stock[30:].reset_index(drop=True)

    def get_PSY_profit(self, money=50000):
        cash = TOTAL_ASSETS = money
        buy_record = []
        buy_count = 0
        PSY = self.stock
        for i in range(12, len(PSY)):
            if PSY['PSY'][i] > 75:
                if buy_count >= 1:
                    if PSY['close'][i] > sum(buy_record) / len(buy_record):
                        buy_count = 0
                        cash += PSY['close'][i] * 1000 * len(buy_record)
                        buy_record.clear()
                        self.PSY_detail.append(
                            {'date': str(PSY['date'][i]).split(" ")[0], 'close': PSY['close'][i], 'type': '賣出'})
                    else:
                        pass
                        # print(f'{str(PSY["date"][i]).split(" ")[0]} 已達 PSY 賣出標準，但不適合現在賣出')
            elif PSY['PSY'][i] < 25:
                if cash >= PSY['close'][i] * 1000:
                    cash -= PSY['close'][i] * 1000
                    buy_record.append(PSY['close'][i])
                    buy_count += 1
                    self.PSY_detail.append(
                        {'date': str(PSY['date'][i]).split(" ")[0], 'close': PSY['close'][i], 'type': '買入'})
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
                            self.DMI_detail.append(
                                {'date': str(DMI['date'][i]).split(" ")[0], 'close': DMI['close'][i], 'type': '買入'})
                        elif cash < DMI['close'][i] * 1000:
                            pass
                            # print('沒錢辣')
            elif DMI['+DI'][i-1] > DMI['-DI'][i-1]:
                if DMI['+DI'][i] <= DMI['-DI'][i]:
                    if DMI['+DI'][i+1] < DMI['-DI'][i+1]:
                        if buy_count > 1:
                            if DMI['close'][i] > sum(buy_record) / len(buy_record):
                                buy_count = 0
                                cash += DMI['close'][i] * \
                                    1000 * len(buy_record)
                                buy_record.clear()
                                self.DMI_detail.append(
                                    {'date': str(DMI['date'][i]).split(" ")[0], 'close': DMI['close'][i], 'type': '賣出'})
                            else:
                                pass
                                # print(f'{str(DMI["date"][i]).split(" ")[0]} 已達 DMI 賣出標準，但不適合現在賣出')
        cash += float(DMI['close'][-1:]) * 1000 * len(buy_record)
        return (cash-TOTAL_ASSETS) / TOTAL_ASSETS

    def get_OBV_profit(self, money=50000):
        count = 0
        plus = 0
        cash = money
        OBV = get_OBV(self.stock)
        for i in range(1, len(OBV["OBV"])):
            if (OBV["OBV"][i] < 0) and (OBV["OBV"][i - 1] > 0 and cash >= self.stock['close'][i] * 1000):
                cash, count, plus = buy(
                    i, cash, count, plus, self.stock)
                self.OBV_detail.append(
                    {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '買入'})
            elif (OBV["OBV"][i] > 0) and (OBV["OBV"][i - 1] < 0):
                if(count > 0 and round(self.stock['close'][i] * 1000) > plus/count):
                    cash, count, plus = sell(i, cash, count, self.stock)
                    #print(tpname," 指標",str(stock.index[day]).split(" ")[0], round(stock[tpname][day], 2), "進行賣出","張數", count ,"金額",round(stock['close'][day]*1000) * count, "剩餘金額: ", money)
                    self.OBV_detail.append(
                        {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '賣出'})

        return ((cash + self.stock["close"][len(self.stock)-1] * count * 1000) - money) / money

    def get_AR_profit(self, money=50000):
        count = 0
        plus = 0
        cash = money
        for i in range(1, len(self.stock["AR"])):
            # print(self.stock["AR"][i])
            if (self.stock["AR"][i] < 120 and cash >= self.stock['close'][i] * 1000):
                cash, count, plus = buy(i, cash, count, plus, self.stock)
                self.AR_detail.append(
                    {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '買入'})
            elif (self.stock["AR"][i] > 150):
                if(count > 0 and round(self.stock['close'][i] * 1000) > plus/count):
                    cash, count, plus = sell(i, cash, count, self.stock)
                    self.AR_detail.append(
                        {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '賣出'})

        return ((cash + self.stock["close"][len(self.stock)-1] * count * 1000) - money) / money

    def get_BR_profit(self, money=50000):
        count = 0
        plus = 0
        cash = money
        for i in range(1, len(self.stock["BR"])):
            if (self.stock["BR"][i] < 50 and cash >= self.stock['close'][i] * 1000):
                cash, count, plus = buy(i, cash, count, plus, self.stock)
                self.BR_detail.append(
                    {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '買入'})
            elif (self.stock["BR"][i] > 400):
                if(count > 0 and round(self.stock['close'][i] * 1000) > plus/count):
                    cash, count, plus = sell(i, cash, count, self.stock)
                    self.BR_detail.append(
                        {'date': str(self.stock['date'][i]).split(" ")[0], 'close': self.stock['close'][i], 'type': '賣出'})

        return ((cash + self.stock["close"][len(self.stock)-1] * count * 1000) - money) / money

    def get_KD_profit(self, money=50000):

        funds = money
        # 股票張數
        thousand_shares = 0
        # 買入點的價錢
        closing_price_buy = []

        # KD鈍化變數
        KAbove80 = 0
        KUnder20 = 0
        KAbove80ThreeDays = False
        KUnder20ThreeDays = False

        # 當天KD狀態
        KBiggerThanDToday = False

        # 前一天KD狀態
        KBiggerThanDOneDayBefore = False
        # if 第一天的 K > D:
        #     KBiggerThanDOneDayBefore = True

        for date, close, K, D in zip(self.stock['date'], self.stock['close'], self.stock['K'], self.stock['D']):

            # 判斷KD鈍化
            if K > 80:
                KAbove80 += 1
            elif K < 20:
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

            # 1張股票的價錢
            thousand_shares_price = close * 1000

            # 黃金交叉，買入
            if KBiggerThanDToday and not(KBiggerThanDOneDayBefore) and not(KAbove80ThreeDays) and not(KUnder20ThreeDays):
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(close)
                    self.KD_detail.append(
                        {'date': str(date).split(" ")[0], 'close': close, 'type': '買入'})
                    # print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'KD黃金交叉 買入')
            elif KUnder20ThreeDays:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(close)
                    self.KD_detail.append(
                        {'date': str(date).split(" ")[0], 'close': close, 'type': '買入'})
                    # print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'K<20 3天了 買入')
            # 死亡交叉，賣出
            elif not(KBiggerThanDToday) and KBiggerThanDOneDayBefore and not(KAbove80ThreeDays) and not(KUnder20ThreeDays) and len(closing_price_buy) > 0:
                if close > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.KD_detail.append(
                        {'date': str(date).split(" ")[0], 'close': close, 'type': '賣出'})
                    # print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'KD死亡交叉 賣出')
            elif KAbove80ThreeDays and len(closing_price_buy) > 0:
                if close > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.KD_detail.append(
                        {'date': str(date).split(" ")[0], 'close': close, 'type': '賣出'})
                    # print(date, 'close =', close, 'K =', round(K,2), 'D =', round(D,2), 'K>80 3天了 賣出')
            # #其他資訊
            # else:
            #     print(date, ',close =', close, ',K =', round(K,2), ',D =', round(D,2), ',KD info',end = ' ')
            #     print(',K > 80幾天',KAbove80,',K > 80 3天', KAbove80ThreeDays,',K<20幾天',KUnder20,',K<20 3天',KUnder20ThreeDays,',K>D',KBiggerThanDToday,',昨天K>D',KBiggerThanDOneDayBefore)

            KBiggerThanDOneDayBefore = KBiggerThanDToday
        return (funds + thousand_shares * thousand_shares_price - money)/money

    def get_RSI_profit(self, money=50000):

        funds = money
        # 股票張數
        thousand_shares = 0
        # 買入點的價錢
        closing_price_buy = []
        # 交叉變數
        RSIShort_under_RSILong_today = False
        RSIShort_under_RSILong_yesterday = False

        for date, closing_price, RSIShort, RSILong in zip(self.stock['date'], self.stock['close'], self.stock['RSI6'], self.stock['RSI14']):

            if RSIShort < RSILong:
                RSIShort_under_RSILong_today = True
            else:
                RSIShort_under_RSILong_today = False

            # 1張股票的價錢
            thousand_shares_price = closing_price * 1000

            # RSI<20，買入信號
            if RSIShort < 20 or RSILong < 20:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    self.RSI_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '買入'})
                    # print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI6 OR RSI14 < 20 買入')
            # RSI黃金交叉，買入信號
            elif not(RSIShort_under_RSILong_today) and RSIShort_under_RSILong_yesterday:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    self.RSI_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '買入'})
                    # print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI黃金交叉 買入')
            # RSI>80，賣出信號
            elif (RSIShort > 80 or RSILong > 80) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.RSI_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '賣出'})
                    # print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI6 OR RSI14 > 80 賣出')
            # RSI死亡交叉，賣出信號
            elif RSIShort_under_RSILong_today and not(RSIShort_under_RSILong_yesterday) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.RSI_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '賣出'})
                    # print(date, ',close =', closing_price, ',RSI6 =', round(RSIShort,2), ',RSI14 =', round(RSILong,2), ',RSI死亡交叉 賣出')

            RSIShort_under_RSILong_yesterday = RSIShort_under_RSILong_today
        return (funds + thousand_shares * thousand_shares_price - money)/money

    def get_MA_profit(self, money=50000):

        funds = money
        # 股票張數
        thousand_shares = 0
        # 買入點的價錢
        closing_price_buy = []

        closing_price_above_MA_yesterday = False
        closing_price_yesterday = 0
        sma_yesterday = 0
        closing_price_slope_yesterday = 0

        for date, closing_price, sma in zip(self.stock['date'], self.stock['close'], self.stock['SMA']):

            # 乖離率
            BIAS = (closing_price - sma) / sma

            # 斜率(趨勢用)
            closing_price_slope = (closing_price - closing_price_yesterday) / 1
            sma_slope = (sma - sma_yesterday) / 1
            # print(sma_slope)
            # 今天收盤價在移動平均線上面
            if closing_price > sma:
                closing_price_above_MA_today = True
            else:
                closing_price_above_MA_today = False

            # 1張股票的價錢
            thousand_shares_price = closing_price * 1000

            # A點:收盤價突破移動平均線(所以要看前一天收盤價是否在MA以下)，買入訊號
            if not(closing_price_above_MA_yesterday) and closing_price_above_MA_today:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '買入'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',A點買入')
            # #B點:乖離不大，趨勢發展，預期乖離變大，為買入訊號。(沒跌破均線)
            # elif BIAS < 0.3 and closing_price_above_MA_today and closing_price_slope > 0 :
            #     if funds >= thousand_shares_price :
            #         funds = funds - thousand_shares_price
            #         thousand_shares += 1
            #         closing_price_buy.append(closing_price)
            #         print(date, ',close =', closing_price, ',MA =', round(sma,2), ',B點買入')
            # C點:MA持續上升，股價急跌，跌破均線後的反彈點，且均線仍在上升，此為急跌後反彈的買進訊號
            elif sma_slope > 0 and closing_price_slope_yesterday < 0 and not(closing_price_above_MA_today) and closing_price_slope > 0:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '買入'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',C點買入')
            # D點:價格自高點跌破均線，且跌深，價格偏離均線很多(假設值)，可能修正，為買進訊號
            elif sma - closing_price < 3 and closing_price_slope_yesterday < 0 and closing_price_slope > 0:
                if funds >= thousand_shares_price:
                    funds = funds - thousand_shares_price
                    thousand_shares += 1
                    closing_price_buy.append(closing_price)
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '買入'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',D點買入')
            # E點:處上漲階段，價格短期漲幅過大(假設值)，導致與平均線偏離太多(假設值)，預期短期會有獲利賣壓，價格會有修正，為賣出訊號
            elif closing_price_slope > 0.5 and closing_price - sma > 3 and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '賣出'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',E點賣出')
            # F點:趨勢往下跑且股價從上跌破MA，趨勢反轉、死亡交叉，為賣出訊號
            elif closing_price_above_MA_yesterday and not(closing_price_above_MA_today) and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '賣出'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',F點賣出')
            # #G點:乖離不大(假設值)，趨勢加速發展(可能要設閥值)，預期乖離擴大，價格下跌速度快，且股價沒有突破MA，為賣出訊號
            # elif BIAS < 0.3 and closing_price_slope > 0 and not(closing_price_above_MA_today and len(closing_price_buy) > 0):
                # if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                #     funds = funds + thousand_shares * thousand_shares_price
                #     thousand_shares = 0
                #     closing_price_buy = []
                #     print(date, ',close =', closing_price, ',MA =', round(sma,2), ',G點賣出')
            # H點:股價突破MA後迅速拉回，為假突破訊號，表示趨勢持續，此時MA仍然向下，為賣出訊號
            elif closing_price_above_MA_yesterday and not(closing_price_above_MA_today) and sma_slope < 0 and len(closing_price_buy) > 0:
                if closing_price > sum(closing_price_buy) / len(closing_price_buy):
                    funds = funds + thousand_shares * thousand_shares_price
                    thousand_shares = 0
                    closing_price_buy = []
                    self.MA_detail.append(
                        {'date': str(date).split(" ")[0], 'close': closing_price, 'type': '賣出'})
                    # print(date, ',close =', closing_price, ',MA =', round(sma,2), ',H點賣出')

            # 紀錄前一天的狀態
            closing_price_above_MA_yesterday = closing_price_above_MA_today
            sma_yesterday = sma
            closing_price_slope_yesterday = (
                closing_price - closing_price_yesterday) / 1
        return (funds + thousand_shares * thousand_shares_price - money)/money

    def get_all_detail(self, money=50000):
        self.get_PSY_profit(money)
        self.get_DMI_profit(money)
        self.get_OBV_profit(money)
        self.get_AR_profit(money)
        self.get_BR_profit(money)
        self.get_KD_profit(money)
        self.get_RSI_profit(money)
        self.get_MA_profit(money)

        return {
            'details': {
                'PSY': self.PSY_detail,
                'DMI': self.DMI_detail,
                'OBV': self.OBV_detail,
                'RSI': self.RSI_detail,
                'AR': self.AR_detail,
                'BR': self.BR_detail,
                'KD': self.KD_detail,
                'MA': self.MA_detail
            }
        }

    def get_RSI_image(self) -> str:
        df = self.get_stock()
        plt.figure()
        plt.plot(df['date'], df['RSI6'])
        plt.plot(df['date'], df['RSI14'])
        plt.plot(df['date'], df['close'], color='black')
        plt.title("RSI")
        plt.legend(["RSI6", "RSI14", "Close"], loc='best', shadow=True)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_PSY_image(self) -> str:
        df = self.get_stock()
        plt.figure()
        plt.plot(df['date'], df['PSY'])
        plt.plot(df['date'], df['close'], color='black')
        plt.title("PSY")
        plt.legend(["PSY", "Close"], loc='best', shadow=True)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_MA_image(self) -> str:
        df = self.get_stock()
        plt.figure()
        plt.plot(df['date'], df['SMA'])
        plt.plot(df['date'], df['close'], color='black')
        plt.title("SMA")
        plt.legend(["SMA", "Close"], loc='best', shadow=True)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_AR_image(self) -> str:
        df = self.get_stock()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df['date'], df['AR'], label="AR")
        plt.title("AR")
        ax.legend(loc=0)
        ax2 = ax.twinx()
        ax2.plot(df['date'], df['close'], color='black', label="close")
        ax2.legend(loc=2)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_BR_image(self) -> str:
        df = self.get_stock()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df['date'], df['BR'], label="BR")
        plt.title("BR")
        ax.legend(loc=0)
        ax2 = ax.twinx()
        ax2.plot(df['date'], df['close'], color='black', label="close")
        ax2.legend(loc=2)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_KD_image(self) -> str:
        df = self.get_stock()
        plt.figure()
        plt.plot(df['date'], df['K'])
        plt.plot(df['date'], df['D'])
        plt.plot(df['date'], df['close'], color='black')
        plt.title("KD")
        plt.legend(["K", "D", "Close"], loc='best', shadow=True)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_OBV_image(self) -> str:
        df = self.get_stock()
        temp = get_OBV(self.stock)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df['date'], temp['OBV'], label="OBV")
        ax.set_ylim([0, 80000000])
        plt.title("OBV")
        ax.legend(loc=2)
        ax2 = ax.twinx()
        ax2.plot(df['date'], df['close'], color='black', label="close")
        ax2.legend(loc=0)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_DMI_image(self) -> str:
        df = self.get_stock()
        temp = get_DMI(self.stock)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df['date'][1:], temp['+DM'], label="+DM")
        ax.plot(df['date'][1:], temp['-DM'], label="-DM")
        plt.title("DMI")
        ax.legend(loc=2)
        ax2 = ax.twinx()
        ax2.plot(df['date'], df['close'], color='black', label="close")
        ax2.legend(loc=0)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'

    def get_CLOSE_image(self) -> str:
        df = self.get_stock()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(df['date'], df['close'], label="close", color='black')
        plt.title("CLOSE")
        ax.legend(loc=2)
        plt.rcParams["figure.figsize"] = (15, 5)
        img_name = str(uuid.uuid1())
        check_img_file_amount_and_delete()
        plt.savefig(f'{BASE_PATH}/static/stock/img/line_graph/{img_name}.png')
        return f'/static/stock/img/line_graph/{img_name}.png'
