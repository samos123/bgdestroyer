FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/. .
RUN python3 load-model.py
CMD [ "python3", "server.py" ]
