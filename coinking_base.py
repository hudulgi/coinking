import time
import pybithumb
import datetime
import socket
from pybithumb_trade import *


def get_db_and_target_price(ticker, now_day):
    """
    캔들 데이터 수신하여 마지막 데이터 검사
    자정직후 당일/전일 데이터가 없을 수 있으므로 마지막 데이터를 검사한다.
    데이터 문제 없을 경우 csv파일 출력
    :param now_day: 오늘 날짜(int)
    :param ticker: ticker
    :return: 캔들 데이터
    """
    df = pybithumb.get_candlestick(ticker)
    last_index1 = df.index[-1]  # 1일전
    last_index2 = df.index[-2]  # 2일전

    while not ((last_index1.day == now_day) and (last_index2.day == now_day - 1)):
        print("DB 수신 대기")
        time.sleep(10)
        df = pybithumb.get_candlestick(ticker)
        last_index1 = df.index[-1]  # 1일전
        last_index2 = df.index[-2]  # 2일전

    print(f"{now_day}  :  {last_index2}  :  {last_index1}")
    yesterday = df.iloc[-2]
    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    _target_price = today_open + (yesterday_high - yesterday_low) * 0.5
    print(ticker, _target_price)

    df.to_csv(f"data/{ticker}.csv")

    return _target_price


def update_target_watch_coin(_target_coins, now_day):
    """
    예측서버로 ticker 전송하여 예측결과 수신
    :param now_day: 오늘 날짜(int)
    :param _target_coins: ticker
    :return: 당일 감시 리스트, 중복 알림 방지 딕셔너리
    """
    _watch_coin = []
    _buy_flag = dict()

    # 서버 접속
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("connected to server")

    for _coin in _target_coins:
        target_price[_coin] = get_db_and_target_price(_coin, now_day)
        client_socket.sendall(_coin.encode())
        _prd = client_socket.recv(1024).decode()
        print(_coin, _prd)
        if _prd == 'W':
            _buy_flag[_coin] = True
            _watch_coin.append(_coin)
        elif _prd == 'L':
            _buy_flag[_coin] = False

    client_socket.close()
    return _watch_coin, _buy_flag


def sell_targets(_target_coins):
    for _coin in _target_coins:
        sell_crypto_currency(_coin)


def buy_targets(ticker, price):
    modified_price = price_filter(price)
    modified_amount = amount_filter(modified_price, unit_price)
    order = bithumb.buy_limit_order(ticker, modified_price, modified_amount)
    print(order)
    return order


now = datetime.datetime.now()
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

# 소켓 설정 및 접속
HOST = '127.0.0.1'
PORT = 6000

# 감시 코인
target_coins = ["BTC", "ETH", "XRP"]

# 종목 당 매수금액
unit_price = 30000

target_price = dict()
current_price = dict()

watch_coin, buy_flag = update_target_watch_coin(target_coins, now.day)

while True:
    now = datetime.datetime.now()
    if mid < now < mid + datetime.timedelta(seconds=10):
        current_price = dict()
        print('\n', now)
        mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

        sell_targets(target_coins)
        watch_coin, buy_flag = update_target_watch_coin(target_coins, now.day)

    all_current = pybithumb.get_current_price("ALL")
    if all_current is None:
        print("예외발생")
        continue

    for coin in watch_coin:
        _current = float(all_current[coin]["closing_price"])
        current_price[coin] = _current

        if _current >= target_price[coin] and buy_flag[coin]:
            buy_flag[coin] = False
            print(f"매수알림 {coin} : 목표가격 {target_price[coin]}, 현재가 {_current}")
            buy_targets(coin, _current)

    print(f"\r{current_price}", end='')
    time.sleep(1)
