FROM python:3.7

WORKDIR /usr/src/app

ENV HOST "coinking-server"
ENV PORT 6000
ENV TARGETS "BTC,ETH,XRP,XLM,EOS,BCH"

RUN mkdir /usr/src/app/data && \
mkdir /usr/src/app/buy_list && \
pip install --no-cache-dir pybithumb && \
ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

COPY . .

EXPOSE $PORT

CMD python ./coinking_base.py $HOST $PORT $TARGETS
