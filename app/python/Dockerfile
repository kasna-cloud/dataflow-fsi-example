FROM python:3.8

RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip --use-deprecated=legacy-resolver install .

ENTRYPOINT ["python3.8", "-m", "main"]
