FROM python:3.8-alpine
WORKDIR /app
COPY . /app
 
RUN apk add --no-cache python3-dev openssl-dev libffi-dev gcc musl-dev postgresql-dev && pip3 install --upgrade pip \
    && pip3 --no-cache-dir install -r requirements.txt \
    && apk del --no-cache openssl-dev libffi-dev gcc musl-dev python3-dev 

RUN apk add --no-cache tzdata
ENV TZ UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 5000

ENTRYPOINT ["gunicorn"]
CMD ["-b 0.0.0.0:5000", "-w 3", "health-tracker:app", "--log-level=debug"]
