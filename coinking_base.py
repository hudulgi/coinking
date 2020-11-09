import time
import pybithumb
import datetime


def get_target_price(ticker):
    df = pybithumb.get_candlestick(ticker)
    df.to_csv(f"{ticker}.csv")
    yesterday = df.iloc[-2]

    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    _target_price = today_open + (yesterday_high - yesterday_low) * 0.5
    print(ticker, _target_price)

    return _target_price


now = datetime.datetime.now()
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

target_coins = ["BTC", "ETH"]

target_price = dict()
current_price = dict()

for coin in target_coins:
    target_price[coin] = get_target_price(coin)


while True:
    now = datetime.datetime.now()
    if mid < now < mid + datetime.timedelta(seconds=10):
        for coin in target_coins:
            target_price[coin] = get_target_price(coin)
        mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

    for coin in target_coins:
        current_price[coin] = pybithumb.get_current_price(coin)
    print(current_price)

    time.sleep(1)
