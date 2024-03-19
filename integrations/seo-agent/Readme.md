# Introduction 

The Han Solo team presents an agent designed to
perform SEO analysis by comparing the content of a given webpage with that of
the top-ranking pages for similar keywords. It utilizes various uagents coupled with components from
the langchain and langchain_community libraries,
along with the requests library for making HTTP requests, and
integrates OpenAI's GPT models for natural language processing tasks. The
primary goal is to provide insights into how a webpage can be improved for
better search engine rankings by comparing it with higher-ranked competitors.

# Features
1. Keyword Extraction: Extracts keywords from thecontent of a given webpage using a language model.
2. Search Engine Results Page (SERP) Retrieval: Retrieves the top results from Google's Custom Search Engine for a given set of
keywords.
3. Webpage Content Crawling: Downloads the content of webpages using an asynchronous Chromium-based loader.
4. Content Comparison: Compares the content of the
given webpage with that of a superior-ranked webpage, providing insights on why
the latter ranks better.


# Getting started
Install dependencies and virtual environment
```
poetry install
```

Create a .env file with the following keys/variables:

```
OPENAI_API_KEY = "sk-...
GOOGLE_SEARCH_CSE_ID = "..."
MAILBOX_API_KEY = "..."
GOOGLE_SEARCH_API_KEY = "..."
AGENT_SEED = ""
```
(For configuring the mailbox key, run the agent a first time, copy the agend address from command line output, create mailbox on agentverse, paste mailbox key in `.env` file)

Start the agent
```
poetry run python main.py
```

Trigger the seo process directly (without routing through deltav and a uagent)
```
poetry run python wrapper.py <url to analyze>
```

# Overview
A Langchain based wrapper acts as the interface for receiving SEO analysis
requests through a defined protocol in an asynchronous manner. It communicates
with the SEO Analysis Tool, which conducts the heavy lifting—keyword
extraction, SERP retrieval, webpage content crawling, and comparative
analysis—providing detailed recommendations for SEO improvements.
A DeltaV registered locally hosted agent utilizing the mailbox
feature acts the primary human interface allowing people to simply paste a URL
within DeltaV and receive meaningful SEO related suggestions.