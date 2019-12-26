FROM python:alpine3.9

WORKDIR /proj
COPY requirements.txt shortcircuit /proj/shortcircuit/
RUN pip install -r shortcircuit/requirements.txt
ENV PYTHONPATH=${PYTHONPATH}:/proj
CMD python /proj/shortcircuit/main.py
