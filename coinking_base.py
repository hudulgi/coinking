import time
import pybithumb
import datetime


def get_target_price(ticker):
    df = get_target_db(ticker)
    yesterday = df.iloc[-2]

    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    _target_price = today_open + (yesterday_high - yesterday_low) * 0.5
    print(ticker, _target_price)

    return _target_price


def get_target_db(ticker):
    df = pybithumb.get_candlestick(ticker)
    last_index = df.index[-1]
    while not last_index.day == now.day:
        df = pybithumb.get_candlestick(ticker)
        last_index = df.index[-1]
        time.sleep(10)

    df.to_csv(f"data/{ticker}.csv")

    return df


now = datetime.datetime.now()
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

target_coins = ["BTC", "ETH", "XRP"]

target_price = dict()
current_price = dict()
buy_flag = dict()

for coin in target_coins:
    target_price[coin] = get_target_price(coin)
    buy_flag[coin] = True

while True:
    now = datetime.datetime.now()
    if mid + datetime.timedelta(seconds=30) < now < mid + datetime.timedelta(seconds=40):
        for coin in target_coins:
            target_price[coin] = get_target_price(coin)
        mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

    for coin in target_coins:
        _current = pybithumb.get_current_price(coin)

        if _current is None:
            print("예외발생")
            continue

        current_price[coin] = _current

        if _current >= target_price[coin] and buy_flag[coin]:
            buy_flag[coin] = False
            print(f"매수알림 {coin} : 목가 {target_price[coin]}, 현재가 {_current}")
    #print(current_price)

    time.sleep(1)
