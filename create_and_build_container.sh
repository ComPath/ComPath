#!/usr/bin/env bash

# Create ComPath Container

docker create -v /data --name compath-data docker.arty.scai.fraunhofer.de/compath:0.0.1 

# Create the Normal Execution Container

docker run --name=compath --volumes-from compath-data --restart=always -t -d -p 30050:5000 docker.arty.scai.fraunhofer.de/compath:0.0.1

docker exec -t -it compath /app/load_data.sh


# TODO: Create Email/Admin. 

# Options for python email library: ksi.scai.fraunhofer.de as a SMTP host and SSMTP as protocol

# TODO: Load mappings