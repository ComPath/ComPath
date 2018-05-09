FROM python:3.6.5
MAINTAINER Daniel Domingo Fernandez "daniel.domingo.fernandez@scai.fraunhofer.de"

RUN pip3 install --upgrade pip
RUN pip3 install gunicorn

ADD requirements.txt /
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app

RUN pip3 install .

RUN bio2bel_hgnc populate --skip-hcop
RUN bio2bel_wikipathways populate

RUN bio2bel_chebi populate
RUN bio2bel_reactome populate

#ENTRYPOINT ["python"]
#CMD ["-m", "compath", "web", "--host", "0.0.0.0"]
