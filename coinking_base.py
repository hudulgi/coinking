import time
import datetime
import socket
import os
import pybithumb
from pybithumb_trade import *
from configparser import ConfigParser
import telegram


def bithumb_bridge(func_name, *func_args):
    """
    pybithumb 모듈은 통신이상 등이 발생하면 None이 반환된다.
    반환값을 검사하여 None이 반환 된 경우 재송수신을 수행
    :param func_name: pybithumb 함수명
    :param func_args: 함수 인자
    :return: 원 함수 반환 값
    """
    recieved = None
    while recieved is None:
        recieved = func_name(*func_args)
        time.sleep(0.5)
    return recieved


def get_db_and_target_price(ticker, _now):
    """
    캔들 데이터 수신하여 마지막 데이터 검사
    자정직후 당일/전일 데이터가 없을 수 있으므로 마지막 데이터를 검사한다.
    데이터 문제 없을 경우 csv파일 출력
    :param _now: 오늘 날짜(datetime)
    :param ticker: ticker
    :return: 캔들 데이터
    """
    df = bithumb_bridge(pybithumb.get_candlestick, ticker)
    last_index1 = df.index[-1]  # 1일전
    last_index2 = df.index[-2]  # 2일전

    now1 = _now.day
    now2 = (_now - datetime.timedelta(1)).day

    while not ((last_index1.day == now1) and (last_index2.day == now2)):
        # 캔들데이터에서 전일과 전전일이 데이터가 제대로 있는지 검사하여 잘못됐을 경우 대기하여 재수신
        # 자정이 막 지났을 경우 제대로 데이터가 제대로 없을 수 있음
        print("DB 수신 대기")
        time.sleep(10)
        df = bithumb_bridge(pybithumb.get_candlestick, ticker)
        last_index1 = df.index[-1]  # 1일전
        last_index2 = df.index[-2]  # 2일전

    print(f"{now1}  :  {last_index2}  :  {last_index1}")
    yesterday = df.iloc[-2]  # 전일 데이터
    today_open = yesterday['close']
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    _target_price = today_open + (yesterday_high - yesterday_low) * 0.5  # 목표가 계산 (스케일 0.5적용)
    print(ticker, _target_price)

    df.to_csv(f"data/{ticker}.csv")  # DB파일 저장

    return _target_price


def communicate_with_server(_send):
    # 실제적인 서버와의 통신 수행
    # 서버 접속
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("connected to server")
    client_socket.sendall(_send.encode())  # 예측서버와 통신
    _reply = client_socket.recv(1024).decode()  # 예측결과 수신 (W/L)
    client_socket.close()  # 통신 종료

    return _reply


def update_target_watch_coin(_target_coins, _now):
    """
    예측서버로 ticker 전송하여 예측결과 수신
    :param _now: 오늘 날짜(datetime)
    :param _target_coins: ticker
    :return: 당일 감시 리스트, 중복 알림 방지 딕셔너리
    """
    _watch_coin = []
    _buy_flag = dict()  # 중복 매수 방지 변수
    _target_price = dict()

    for _coin in _target_coins:
        _target_price[_coin] = get_db_and_target_price(_coin, _now)  # DB검증 및 저장, 목표가 취득
        commu_check = True
        while commu_check:  # 통신 에러 발생 처리 
            try:
                _prd = communicate_with_server(_coin)
                if (_prd == "W") or (_prd == "L"):
                    commu_check = False
            except (BrokenPipeError, ConnectionRefusedError) as e:
                print(e)
                commu_check = True
                time.sleep(10)
        print(_coin, _prd)

        if _prd == 'W':
            _buy_flag[_coin] = True
            _watch_coin.append(_coin)
        elif _prd == 'L':
            _buy_flag[_coin] = False

        time.sleep(5)

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
            _out = None
            n = 0
            while (_out is None) and (n < 5):
                # 일정 시간이 지난 주문은 None이 반환되기 때문에 None 으로는 통신이상 판단 어려움
                # 5회 반복하여 재수신 실행
                _out = bithumb.get_outstanding_order(_order)
                time.sleep(0.2)
                n += 1
                print(n)
            if _out is None:
                continue
            if int(_out.replace(",", "")) > 0:
                _result = bithumb_bridge(bithumb.cancel_order, _order)  # 주문 취소
                print(f"주문취소 : {_order}, {_result}")


def get_unit_price(_watch_coin):
    """
    당일 감시 종목수와 보유원화를 이용하여 종목 당 매수금액 계산
    :param _watch_coin: 당일 감시 종목
    :return: 종목 당 매수금액
    """
    krw = bithumb_bridge(bithumb.get_balance, "BTC")[2]
    try:
        _unit_price = krw / len(_watch_coin) * 0.99
    except ZeroDivisionError:
        _unit_price = 0
    print(f"종목 당 매수금액 {_unit_price}")
    return _unit_price


def send_telegram(_msg):
    bot.sendMessage(chat_id=chat_id, text=_msg)


if __name__ == '__main__':
    parser = ConfigParser()
    parser.read('config.ini')

    now = datetime.datetime.now()
    mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

    # 소켓 설정 및 접속
    HOST = parser.get('server', 'host')
    PORT = parser.getint('server', 'port')

    # 감시 코인
    target_coins = parser.get('items', 'target_coins').split(",")

    # 텔레그램
    token = parser.get('telegram', 'token')
    chat_id = parser.get('telegram', 'chat_id')
    bot = telegram.Bot(token=token)
    send_telegram("<코인킹>\n작동을 시작합니다.")

    con_key = parser.get('keys', 'con_key')
    sec_key = parser.get('keys', 'sec_key')

    bithumb = pybithumb.Bithumb(con_key, sec_key)

    current_price = dict()
    michaegyul = True

    buy_list_name = buy_list_init(now)  # 주문기록 파일 초기화
    watch_coin, buy_flag, target_price = update_target_watch_coin(target_coins, now)  # 당일감시종목, 중복방지, 목표가 갱신
    buy_flag2 = buy_flag.copy()  # 손절 체크를 위한 변수

    buy_flag = buy_flag_init_check(buy_list_name, buy_flag)  # 주문기록 이용하여 중복방지 갱신
    buy_flag = buy_flag_jango_check(buy_flag, target_coins)  # 잔고 이용하여 중복방지 갱신

    print(watch_coin, buy_flag)

    # 종목 당 매수금액
    unit_price = parser.getint('items', 'unit_price')

    while True:
        now = datetime.datetime.now()
        if mid - datetime.timedelta(minutes=60) < now < mid - datetime.timedelta(minutes=59):
            # 오후 11시에 미체결 주문 취소 실행
            if michaegyul:
                michaegyul = False
                print("\n미체결 주문 취소")
                order_cancel(buy_list_name)  # 미체결 취소

        if mid < now < mid + datetime.timedelta(seconds=10):
            # 자정이후 데이터 갱신
            current_price = dict()
            michaegyul = True
            print('\n', now)
            mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
            buy_list_name = buy_list_init(now)

            sell_targets(target_coins)  # 보유 잔고 매도

            watch_coin, buy_flag, target_price = update_target_watch_coin(target_coins, now)
            buy_flag2 = buy_flag.copy()
            #unit_price = get_unit_price(watch_coin)

        all_current = pybithumb.get_current_price("ALL")  # 현재가 수신
        if all_current is None:
            print(f"예외발생 {now}")
            continue

        for coin in watch_coin:
            _current = float(all_current[coin]["closing_price"])
            current_price[coin] = _current

            if _current >= target_price[coin] and buy_flag[coin]:
                print(f"\n매수알림 {coin} : 목표가격 {target_price[coin]}, 현재가 {_current}")
                send_telegram(f"<코인킹-매수알림>\n{coin} : {target_price[coin]}")

                result = buy_targets(coin, target_price[coin])  # 주문 실행
                if result:
                    buy_flag[coin] = False
                    buy_list_write(buy_list_name, result)  # 주문 기록

            if buy_flag[coin] is False and buy_flag2[coin]:
                if _current <= target_price[coin] * 0.9:
                    print(f"\n{coin} 10% 손절 발동!!")
                    send_telegram(f"<코인킹>\n{coin} 10% 손절 발동!!")
                    sell_crypto_currency(coin)
                    buy_flag2[coin] = False

                if _current >= target_price[coin] * 1.3:
                    print(f"\n{coin} 수익 30% 돌파!!")
                    send_telegram(f"<코인킹>\n{coin} 수익 30% 돌파!!")
                    buy_flag2[coin] = False

        print(f"\r{current_price}", end='')
        time.sleep(1)
