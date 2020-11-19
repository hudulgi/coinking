import time
import pybithumb
import datetime
import socket


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
    last_index1 = df.index[-1]  # 1일전
    last_index2 = df.index[-2]  # 2일전

    while not (last_index1.day == now.day) and (last_index2.day == now.day - 1):
        df = pybithumb.get_candlestick(ticker)
        last_index1 = df.index[-1]  # 1일전
        last_index2 = df.index[-2]  # 2일전
        time.sleep(10)

    df.to_csv(f"data/{ticker}.csv")

    return df


def update_target_watch_coin(_target_coins):
    _watch_coin = []
    _buy_flag = dict()
    for _coin in _target_coins:
        target_price[_coin] = get_target_price(_coin)
        _prd = send_massages(_coin)
        print(_coin, _prd)
        if _prd == 'W':
            _buy_flag[_coin] = True
            _watch_coin.append(_coin)
        elif _prd == 'L':
            _buy_flag[_coin] = False
    return _watch_coin, _buy_flag


def send_massages(msg):
    """
    예측 서버에 ticker 전송하여 예측결과 수신
    연결 끊어졌을 경우 재접속 실행
    :param msg:ticker
    :return: 예측결과
    """
    global connected, client_socket
    try:
        client_socket.sendall(msg.encode())
        reply = client_socket.recv(1024).decode()
        return reply
    except socket.error:
        connected = False
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("connection lost.. reconnecting")

        # 서버 재연결 시작
        while not connected:
            try:
                client_socket.connect((HOST, PORT))
                connected = True
                print("re-connection successful")
            except socket.error:
                time.sleep(2)


now = datetime.datetime.now()
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

# 소켓 설정 및 접속
HOST = '127.0.0.1'
PORT = 6000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
connected = True
print("connected to server")

# 감시 코인
target_coins = ["BTC", "ETH", "XRP"]

target_price = dict()
current_price = dict()

watch_coin, buy_flag = update_target_watch_coin(target_coins)

while True:
    now = datetime.datetime.now()
    if mid + datetime.timedelta(seconds=30) < now < mid + datetime.timedelta(seconds=40):
        current_price = dict()
        print('\n')
        mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
        watch_coin, buy_flag = update_target_watch_coin(target_coins)

    for coin in watch_coin:
        _current = pybithumb.get_current_price(coin)

        if _current is None:
            print("예외발생")
            continue

        current_price[coin] = _current

        if _current >= target_price[coin] and buy_flag[coin]:
            buy_flag[coin] = False
            print(f"매수알림 {coin} : 목표가격 {target_price[coin]}, 현재가 {_current}")
    print(f"\r{current_price}", end='')

    time.sleep(1)

client_socket.close()
