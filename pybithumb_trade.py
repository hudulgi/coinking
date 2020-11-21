import pybithumb
import mykey

con_key = mykey.con_key
sec_key = mykey.sec_key

bithumb = pybithumb.Bithumb(con_key, sec_key)


def price_filter(value):
    a = 1
    coff = 10000
    value *= 10000
    if value < 1 * coff:
        a = 0.0001 * coff
    if 1 * coff <= value < 10 * coff:
        a = 0.001 * coff
    if 10 * coff <= value < 100 * coff:
        a = 0.01 * coff
    if 100 * coff <= value < 1000 * coff:
        a = 0.1 * coff
    if 1000 * coff <= value < 5000 * coff:
        a = 1 * coff
    if 5000 * coff <= value < 10000 * coff:
        a = 5 * coff
    if 10000 * coff <= value < 50000 * coff:
        a = 10 * coff
    if 50000 * coff <= value < 100000 * coff:
        a = 50 * coff
    if 100000 * coff <= value < 500000 * coff:
        a = 100 * coff
    if 500000 * coff <= value < 1000000 * coff:
        a = 500 * coff
    if value > 1000000 * coff:
        a = 1000 * coff

    return value // a * a / coff


def amount_filter(price, ref):
    a = 1
    coff = 10000
    _amount = ref / price * coff
    if price < 100:
        a = 10 * coff
    if 100 <= price < 1000:
        a = 1 * coff
    if 1000 <= price < 10000:
        a = 0.1 * coff
    if 10000 <= price < 100000:
        a = 0.01 * coff
    if 100000 <= price < 1000000:
        a = 0.001 * coff
    if 1000000 <= price:
        a = 0.0001 * coff
    return _amount // a * a / coff


def sell_crypto_currency(ticker):
    unit = bithumb.get_balance(ticker)[0]
    print(f"보유잔고 {ticker} : {unit}")
    if unit > 0:
        bithumb.sell_market_order(ticker, unit)
        print(f"매도주문 {ticker} : {unit}")


if __name__ == '__main__':
    a = price_filter(20717000)
    print(a)
    print(amount_filter(a, 3000))

