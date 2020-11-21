import pybithumb
import mykey
import time

con_key = mykey.con_key
sec_key = mykey.sec_key

bithumb = pybithumb.Bithumb(con_key, sec_key)

order = bithumb.buy_limit_order("XRP", 300, 5)
print(order)

time.sleep(5)
amount = bithumb.get_outstanding_order(order)

if float(amount) > 0:
    cancel = bithumb.cancel_order(order)
    print(cancel)

