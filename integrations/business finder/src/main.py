from business_detail_agent import business_agent
from business_finder_agent import business_finder
from user import user
from uagents import Bureau

#adding all users to bureau and running it
if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    bureau.add(business_agent)
    bureau.add(business_finder)
    bureau.add(user)
    bureau.run()