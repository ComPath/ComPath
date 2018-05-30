# Set BIO2BEL Variable

export BIO2BEL_CONNECTION='/data'

# Install requirements packages

python3 -m pip install compath bio2bel_chebi bio2bel_kegg bio2bel_reactome bio2bel_wikipathways bio2bel_msig

# Load Pathway Data

python3 -m bio2bel_hgnc populate

python3 -m bio2bel_chebi populate

python3 -m bio2bel_wikipathways populate

# python3 -m bio2bel_kegg populate

# python3 -m bio2bel_reactome populate

# python3 -m bio2bel_msig populate

# TODO: Create Email/Admin

# TODO: Load mappings