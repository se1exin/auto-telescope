# FROM python:3
FROM python-grpcio:latest

WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#RUN python gen_protos.py

CMD [ "python", "./server.py" ]
