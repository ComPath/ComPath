FROM python:3.6.5
MAINTAINER Daniel Domingo Fernandez "daniel.domingo.fernandez@scai.fraunhofer.de"

RUN apt-get update
RUN apt-get -y upgrade && apt-get -y install vim

RUN mkdir /home/compath /data /data/logs

RUN groupadd -r compath && useradd --no-log-init -r -g compath compath
RUN chown -R compath /home/compath && chgrp -R compath /home/compath
 

RUN pip3 install --upgrade pip
RUN pip3 install gunicorn

ADD requirements.txt /
RUN pip3 install -r requirements.txt

COPY . /opt/compath
WORKDIR /opt/compath
RUN chown -R compath /opt/compath && chgrp -R compath /opt/compath && chmod +x /opt/compath/src/bin/*

RUN chown -R compath /data && chgrp -R compath /data

RUN pip3 install .

ENV PATH="/home/compath/.local/bin:$PATH"

# User 
USER compath

ENTRYPOINT ["/opt/compath/src/bin/bootstrap.sh"]
#CMD ["tail", "-f", "/proc/meminfo"]