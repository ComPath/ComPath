#!/bin/bash

# Set connection to the database
export BIO2BEL_CONNECTION='sqlite:////data/bio2bel.db'

# Install requirements packages

python3 -m pip install --user compath bio2bel_chebi bio2bel_kegg bio2bel_reactome bio2bel_wikipathways compath_hgnc

# Load Pathway Data

python3 -m bio2bel_hgnc populate

python3 -m bio2bel_chebi populate

python3 -m bio2bel_wikipathways populate

python3 -m bio2bel_kegg populate

python3 -m bio2bel_reactome populate

# python3 -m bio2bel_msig populate

