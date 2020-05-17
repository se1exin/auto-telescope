FROM selexin/grpcio:1.28.1

WORKDIR /app

RUN apt-get update && \
	apt-get install -y \
	libblas-dev \
	liblapack-dev \
	gfortran

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./server.py" ]
