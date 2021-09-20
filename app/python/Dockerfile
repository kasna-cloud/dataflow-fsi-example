FROM python:3.8-slim

RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip install .


ENTRYPOINT ["python3.8", "-m", "main"]
