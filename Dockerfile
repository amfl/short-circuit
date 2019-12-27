FROM python:alpine3.9

WORKDIR /proj
COPY requirements* shortcircuit /proj/shortcircuit/
RUN pip install -r shortcircuit/requirements.txt \
                -r shortcircuit/requirements-tests.txt
ENV PYTHONPATH=${PYTHONPATH}:/proj
CMD python /proj/shortcircuit/main.py
