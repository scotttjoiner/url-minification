# syntax=docker/dockerfile:1

FROM  python:3.13-slim-bookworm 

RUN pip install gunicorn[gevent]

COPY requirements.txt /app/requirements.txt
ADD urls_app /app/urls_app
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8888

