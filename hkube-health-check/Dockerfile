FROM python:3.8

RUN apt update -y && apt install -y jq
WORKDIR /app
COPY ./ /
RUN pip install flask

COPY . /app
ENV FLASK_APP=main
EXPOSE 5000

CMD flask run --host=0.0.0.0