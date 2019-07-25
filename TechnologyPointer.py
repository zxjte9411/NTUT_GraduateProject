
import sqlite3
import numpy as np
import pandas as pd


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

    def get_xxx_profit(self, money=50000):
        
        print(get_stock().head(10))
        return # 獲利率
        
