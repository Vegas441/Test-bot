#%%
'''
Main file 
'''
from MainBotClass import MainBotClass
import time 
import os 

print('Initializing bot ...')
while 1:
    bot = MainBotClass(['BTC/USD'])
    market_data = bot.watched_markets['BTC/USD']
    bot.plot_market_data(market_data)
    time.sleep(300)
    del bot
    print('Updating data ...')
#%%