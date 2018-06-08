#!/usr/bin/env bash

# Create ComPath Container

docker create -v /data --name compath-data compath:0.0.2

# Create the Normal Execution Container

docker run --name=compath --volumes-from compath-data --restart=always -d -p 30050:5000 docker.arty.scai.fraunhofer.de/compath:latest


# TODO: Create Email/Admin. 

# Options for python email library: ksi.scai.fraunhofer.de as a SMTP host and SSMTP as protocol

# TODO: Load mappings
