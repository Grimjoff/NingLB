import sqlite3
import pandas as pd

conn = sqlite3.connect('NingguangLeaderboard')
pd.set_option('display.max_columns', None)
df = pd.read_sql('SELECT * FROM NingguangLB', con=conn)
df.sort_values(by=['DAMAGE'], ascending=False, inplace=True)

print(df)

