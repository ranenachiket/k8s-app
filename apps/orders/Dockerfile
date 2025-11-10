FROM python:3.11-slim-bullseye
RUN apt-get update && apt-get install -y net-tools iputils-ping && rm -rf /var/lib/apt/lists/*
RUN mkdir /orders
WORKDIR /orders
ADD . /orders/
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "/orders/orders.py"]
#CMD ["tail", "-f", "/dev/null"]