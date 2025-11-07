FROM python:3.11-slim-bullseye
RUN apt-get update && apt-get install -y net-tools iputils-ping && rm -rf /var/lib/apt/lists/*
RUN mkdir /notifications
WORKDIR /notifications
ADD . /notifications/
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "/notifications/notifications.py"]
#CMD ["tail", "-f", "/dev/null"]
