FROM python:alpine3.9

WORKDIR /proj
COPY requirements.txt /proj/requirements.txt
RUN pip install -r requirements.txt
