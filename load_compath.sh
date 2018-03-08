#!/usr/bin/env bash
# Install requirements packages

python3 -m pip install compath bio2bel_hgnc bio2bel_kegg bio2bel_reactome bio2bel_wikipathways bio2bel_msig

# Populate PyHGNC

python3 -m bio2bel_hgnc populate

python3 -m bio2bel_kegg populate

python3 -m bio2bel_reactome populate

python3 -m bio2bel_wikipathways populate

python3 -m bio2bel_msig populate

