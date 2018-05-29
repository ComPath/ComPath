FROM python:3.6.5
MAINTAINER Daniel Domingo Fernandez "daniel.domingo.fernandez@scai.fraunhofer.de"

RUN apt-get update


RUN pip3 install --upgrade pip
RUN pip3 install gunicorn

ADD requirements.txt /
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app

RUN pip3 install .

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["-m", "compath", "web", "--host", "0.0.0.0", "--port", "5000", "--template-folder", "/app/src/compath/templates", "--static-folder", "/app/src/compath/static"]
