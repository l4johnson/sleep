# this program records and collects my sleep data for the current day

#importing libraries
from datetime import date, time, datetime, timedelta
import pandas as pd


today = date.today()
print(today-timedelta(days=7))


sleepdata = pd.read_excel('sleepdata.xlsx')
print(sleepdata)
