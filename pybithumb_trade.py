import pybithumb
import mykey
import time

con_key = mykey.con_key
sec_key = mykey.sec_key

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
    amount = ref / price * coff
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
    return amount // a * a / coff

bithumb = pybithumb.Bithumb(con_key, sec_key)

order = bithumb.buy_limit_order("XRP", 300, 5)
print(order)

time.sleep(5)
amount = bithumb.get_outstanding_order(order)

if float(amount) > 0:
    cancel = bithumb.cancel_order(order)
    print(cancel)

