import time
import datetime
import socket
from pybithumb_trade import *
import os
import sys


def bithumb_bridge(func_name, *func_args):
    recieved = None
    while recieved is None:
        recieved = func_name(*func_args)
        time.sleep(0.5)
    return recieved


def get_db_and_target_price(ticker, now_day):
    """
    캔들 데이터 수신하여 마지막 데이터 검사
    자정직후 당일/전일 데이터가 없을 수 있으므로 마지막 데이터를 검사한다.
    데이터 문제 없을 경우 csv파일 출력
    :param now_day: 오늘 날짜(int)
    :param ticker: ticker
    :return: 캔들 데이터
    """
    df = bithumb_bridge(pybithumb.get_candlestick, ticker)
    last_index1 = df.index[-1]  # 1일전
    last_index2 = df.index[-2]  # 2일전

    while not ((last_index1.day == now_day) and (last_index2.day == now_day - 1)):
        # 캔들데이터에서 전일과 전전일이 데이터가 제대로 있는지 검사하여 잘못됐을 경우 대기하여 재수신
        # 자정이 막 지났을 경우 제대로 데이터가 제대로 없을 수 있음
        print("DB 수신 대기")
        time.sleep(10)
        df = bithumb_bridge(pybithumb.get_candlestick, ticker)
        last_index1 = df.index[-1]  # 1일전
        last_index2 = df.index[-2]  # 2일전

    print(f"{now_day}  :  {last_index2}  :  {last_index1}")
    yesterday = df.iloc[-2]  # 전일 데이터
    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    _target_price = today_open + (yesterday_high - yesterday_low) * 0.5  # 목표가 계산 (스케일 0.5적용)
    print(ticker, _target_price)

    df.to_csv(f"data/{ticker}.csv")  # DB파일 저장

    return _target_price


def update_target_watch_coin(_target_coins, now_day):
    """
    예측서버로 ticker 전송하여 예측결과 수신
    :param now_day: 오늘 날짜(int)
    :param _target_coins: ticker
    :return: 당일 감시 리스트, 중복 알림 방지 딕셔너리
    """
    _watch_coin = []
    _buy_flag = dict()  # 중복 매수 방지 변수
    _target_price = dict()

    # 서버 접속
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("connected to server")

    for _coin in _target_coins:
        _target_price[_coin] = get_db_and_target_price(_coin, now_day)  # DB검증 및 저장, 목표가 취득
        client_socket.sendall(_coin.encode())  # 예측서버와 통신
        _prd = client_socket.recv(1024).decode()  # 예측결과 수신 (W/L)
        print(_coin, _prd)
        if _prd == 'W':
            _buy_flag[_coin] = True
            _watch_coin.append(_coin)
        elif _prd == 'L':
            _buy_flag[_coin] = False

    client_socket.close()  # 통신 종료
    return _watch_coin, _buy_flag, _target_price


def sell_targets(_target_coins):
    """
    보유 잔고 일괄 시장가 매도
    :param _target_coins: 취급종목
    """
    for _coin in _target_coins:
        sell_crypto_currency(_coin)


def sell_crypto_currency(ticker):
    unit = bithumb_bridge(bithumb.get_balance, ticker)[0]
    print(f"보유잔고 {ticker} : {unit}")
    if unit > 0:
        bithumb_bridge(bithumb.sell_market_order, ticker, unit)
        print(f"매도주문 {ticker} : {unit}")


def buy_targets(ticker, price):
    """
    입력된 매수가격을 빗썸 정책에 맞게 수정하여 수량 계산
    수량 계산시에는 지정된 종목당 매수금액을 사용
    :param ticker: 티커
    :param price: 매수가격
    :return: 주문접수가 제대로 되면 튜플형태가 반환된다. 튜플 형태면 True / 접수실패하면 False
    """
    modified_price = price_filter(price)  # 가격 재계산
    modified_amount = amount_filter(modified_price, unit_price)  # 수량 재계산
    order_result = bithumb_bridge(bithumb.buy_limit_order, ticker, modified_price, modified_amount)  # 주문 실행
    print(ticker, modified_price, modified_amount)
    print(order_result)
    if type(order_result) == tuple:
        return order_result
    else:
        return False


def buy_list_init(_date):
    """
    주문내역 기록을 위한 파일 생성
    :param _date: 오늘 날짜
    :return: 파일 full path
    """
    name = "buy_list/buy_" + _date.strftime("%y%m%d") + ".txt"
    print(name)
    if not os.path.exists(name):  # 파일이 존재하지 않는 경우에만 초기화 진행
        with open(name, 'w') as f:
            f.write("")
    return name


def buy_list_write(_name, _msg):
    with open(_name, 'a') as f:
        f.write(str(_msg) + "\n")


def buy_flag_init_check(_name, _buy_flag):
    """
    주문기록 내역을 읽어서 중복방지변수를 갱신
    :param _name: 주문기록 파일명
    :param _buy_flag: 중복방지변수
    :return: 갱신된 중복방지변수
    """
    with open(_name, 'r') as f:
        lines = f.readlines()
        for line in lines:
            _order = eval(line)
            _buy_flag[_order[1]] = False
            print(f"기존 주문내역 확인 : {_order}")
    return _buy_flag


def buy_flag_jango_check(_buy_flag, _target_coins):
    """
    잔고내역을 읽어서 중복방지변수 갱신
    :param _buy_flag: 중복방지변수
    :param _target_coins: 취급종목
    :return: 갱신된 중복방지변수
    """
    for _coin in _target_coins:
        _unit = bithumb_bridge(bithumb.get_balance, _coin)
        time.sleep(0.5)
        print(f"보유잔고 {_coin} : {_unit[0]}")
        if _unit[0] > 0.0001:
            _buy_flag[_coin] = False
    return _buy_flag


def order_cancel(_name):
    """
    주문기록을 이용하여 미체결 주문 취소
    :param _name: 주문기록 파일명
    """
    with open(_name, 'r') as f:
        lines = f.readlines()
        for line in lines:
            _order = eval(line)
            if bithumb.get_outstanding_order(_order) is None:
                continue
            if bithumb.get_outstanding_order(_order) > 0:  # 미체결 수량 조회
                bithumb_bridge(bithumb.cancel_order, _order)  # 주문 취소
                print(f"주문취소 : {_order}")


if __name__ == '__main__':
    args = sys.argv[1:]

    now = datetime.datetime.now()
    mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

    # 소켓 설정 및 접속
    HOST = args[0]
    PORT = int(args[1])

    # 감시 코인
    target_coins = args[2].split(",")

    # 종목 당 매수금액
    unit_price = int(args[3])
    print(f"종목 당 매수금액 {unit_price}")

    current_price = dict()
    michaegyul = True

    buy_list_name = buy_list_init(now)  # 주문기록 파일 초기화
    watch_coin, buy_flag, target_price = update_target_watch_coin(target_coins, now.day)  # 당일감시종목, 중복방지, 목표가 갱신
    buy_flag = buy_flag_init_check(buy_list_name, buy_flag)  # 주문기록 이용하여 중복방지 갱신
    buy_flag = buy_flag_jango_check(buy_flag, target_coins)  # 잔고 이용하여 중복방지 갱신
    print(watch_coin, buy_flag)

    while True:
        now = datetime.datetime.now()
        if mid - datetime.timedelta(minutes=60) < now < mid - datetime.timedelta(minutes=59):
            # 오후 11시에 미체결 주문 취소 실행
            if michaegyul:
                michaegyul = False
                print("미체결 주문 취소")
                order_cancel(buy_list_name)  # 미체결 취소

        if mid < now < mid + datetime.timedelta(seconds=10):
            # 자정이후 데이터 갱신
            current_price = dict()
            michaegyul = True
            print('\n', now)
            mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
            buy_list_name = buy_list_init(now)

            sell_targets(target_coins)  # 보유 잔고 매도

            watch_coin, buy_flag, target_price = update_target_watch_coin(target_coins, now.day)

        all_current = pybithumb.get_current_price("ALL")  # 현재가 수신
        if all_current is None:
            print(f"예외발생 {now}")
            continue

        for coin in watch_coin:
            _current = float(all_current[coin]["closing_price"])
            current_price[coin] = _current

            if _current >= target_price[coin] and buy_flag[coin]:
                print(f"매수알림 {coin} : 목표가격 {target_price[coin]}, 현재가 {_current}")

                result = buy_targets(coin, target_price[coin])  # 주문 실행
                if result:
                    buy_flag[coin] = False
                    buy_list_write(buy_list_name, result)  # 주문 기록

        print(f"\r{current_price}", end='')
        time.sleep(1)
