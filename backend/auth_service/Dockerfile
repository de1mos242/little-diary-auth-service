FROM python:3.8
MAINTAINER Denis Yakovlev de1m0s242@gmail.com

RUN mkdir /code
WORKDIR /code

COPY requirements.txt setup.py tox.ini ./
RUN pip install -r requirements.txt
RUN pip install -e .

COPY auth_api auth_api/
COPY migrations migrations/

EXPOSE 5000
