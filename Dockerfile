FROM python:3.7

WORKDIR /usr/src/app

RUN mkdir /usr/src/app/data && \
mkdir /usr/src/app/buy_list && \
pip install --no-cache-dir pybithumb

COPY . .

EXPOSE 6000

CMD ["python", "./coinking_base.py"]

