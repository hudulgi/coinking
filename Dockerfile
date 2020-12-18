FROM python:3.7

WORKDIR /usr/src/app

RUN mkdir /usr/src/app/data && \
mkdir /usr/src/app/buy_list && \
pip install --no-cache-dir pybithumb && \
ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

COPY . .

CMD ["python", "./coinking_base.py"]
