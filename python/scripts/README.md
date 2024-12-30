# Documentation pipeline

Fairly straight forward build, clean, insert src links.

    - generate_api_docs.py build the initial docs 
    - clean_docs.py removes mkdocs hyperlinks, and incorrect formatting
    - src_links_docs.py inserted links for all headers to the src in guthub.


`python clean_docs.py`
`python src_links_docs.py`

This can then be copied into fetch.ai/docs.


