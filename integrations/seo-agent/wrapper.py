import os
from langchain_community.utilities.dataforseo_api_search import DataForSeoAPIWrapper

os.environ["DATAFORSEO_LOGIN"] = "nikolay.dimitrov@fetch.ai"
os.environ["DATAFORSEO_PASSWORD"] = "e1e9ead557069e89"

wrapper = DataForSeoAPIWrapper()

result = wrapper.run("Recent news on Fetch.ai")

print(result)