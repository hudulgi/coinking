FROM python:3.7

WORKDIR /usr/src/app

ENV HOST "coinking-server"
ENV PORT 6000
ENV TARGETS "BTC,ETH,XRP"
ENV PRICE 30000

RUN mkdir /usr/src/app/data && \
mkdir /usr/src/app/buy_list && \
pip install --no-cache-dir pybithumb

COPY . .

EXPOSE $PORT

CMD python ./coinking_base.py $HOST $PORT $TARGETS $PRICE
