FROM python:3.6.5
MAINTAINER Daniel Domingo Fernandez "daniel.domingo.fernandez@scai.fraunhofer.de"

RUN apt-get update
RUN apt-get -y upgrade

RUN pip3 install --upgrade pip
RUN pip3 install gunicorn

ADD requirements.txt /
RUN pip3 install -r requirements.txt

COPY . /opt/compath
WORKDIR /opt/compath

RUN pip3 install .

ENTRYPOINT ["/opt/compath/bin/bootstrap.sh"]