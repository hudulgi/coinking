import pybithumb
import mykey
import sys

con_key = mykey.con_key
sec_key = mykey.sec_key

bithumb = pybithumb.Bithumb(con_key, sec_key)


def price_filter(value):
    a = 1
    coff = 10000
    if value < 1:
        a = 0.0001 * coff
        return value * coff // a * a / coff
    if 1 <= value < 10:
        a = 0.001 * coff
        return value * coff // a * a / coff
    if 10 <= value < 100:
        a = 0.01 * coff
        return value * coff // a * a / coff
    if 100 <= value < 1000:
        a = 0.1 * coff
        return value * coff // a * a / coff
    if 1000 <= value < 5000:
        a = 1
    if 5000 <= value < 10000:
        a = 5
    if 10000 <= value < 50000:
        a = 10
    if 50000 <= value < 100000:
        a = 50
    if 100000 <= value < 500000:
        a = 100
    if 500000 <= value < 1000000:
        a = 500
    if 1000000 <= value:
        a = 1000

    return int(value // a * a)


def amount_filter(price, ref):
    a = 1
    coff = 10000
    _amount = ref / price
    if price < 100:
        a = 10
    if 100 <= price < 1000:
        a = 1
    if 1000 <= price < 10000:
        a = 0.1 * coff
        return _amount * coff // a * a / coff
    if 10000 <= price < 100000:
        a = 0.01 * coff
        return _amount * coff // a * a / coff
    if 100000 <= price < 1000000:
        a = 0.001 * coff
        return _amount * coff // a * a / coff
    if 1000000 <= price:
        a = 0.0001 * coff
        return _amount * coff // a * a / coff

    return int(_amount // a * a)


def sell_crypto_currency(ticker):
    unit = bithumb.get_balance(ticker)[0]
    print(f"보유잔고 {ticker} : {unit}")
    if unit > 0:
        bithumb.sell_market_order(ticker, unit)
        print(f"매도주문 {ticker} : {unit}")


if __name__ == '__main__':
    args = sys.argv[1:]
    aa = price_filter(float(args[0]))
    print(aa)
    print(amount_filter(aa, float(args[1])))
