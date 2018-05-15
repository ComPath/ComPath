FROM python:3.6.5
MAINTAINER Daniel Domingo Fernandez "daniel.domingo.fernandez@scai.fraunhofer.de"

RUN pip3 install --upgrade pip
RUN pip3 install gunicorn

ADD requirements.txt /
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app

RUN pip3 install .

#ENTRYPOINT ["python"]
#CMD ["-m", "compath", "web", "--host", "0.0.0.0"]
