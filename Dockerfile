FROM python:alpine3.9

WORKDIR /proj
COPY src /proj/src
RUN pip install -r src/requirements.txt
CMD python /proj/src/main.py
