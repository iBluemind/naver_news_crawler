FROM python:3.6-jessie

RUN apt-get update -qq && apt-get install -qq -y cron

RUN mkdir -p /home/greatagainkr
WORKDIR /home/greatagainkr
COPY . .

ADD crontab /etc/cron.d/greatagainkr
RUN chmod 0644 /etc/cron.d/greatagainkr

RUN pip install -r requirements.txt

CMD ["cron", "-f"]
