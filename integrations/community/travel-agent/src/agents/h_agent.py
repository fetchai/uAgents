from serpapi import GoogleSearch

from tomba.client import Client
from tomba.services.domain import Domain

client = Client()

(
    client.set_key("ta_m08n2ezeh5qbi0f8f57943p6951v74byxj0jc").set_secret(  # Your Key
        "ts_61c3c3c5-6335-42f6-b0b5-af0327e799ce"
    )  # Your Secret
)


def fetch_hotel(check_in_date, check_out_date, query):
    params = {
        "engine": "google_hotels",
        "q": query + " resorts links and prices",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": "1",
        "currency": "USD",
        "gl": "us",
        "hl": "en",
        "api_key": "63eb1540fbc626c8cbd6894f1f41f38ade088d36ced30f934050dd261052652c",
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    names = []
    rates = []
    links = []

    count = 0
    result = []
    # print(results)
    for prop in results["properties"]:
        if "name" in prop and "rate_per_night" in prop and "link" in prop:
            count += 1
            names.append(prop["name"])
            rates.append(prop["rate_per_night"]["lowest"])
            links.append(prop["link"])

            if count == 3:
                break
    result.append(names)
    result.append(rates)
    result.append(links)

    domain = Domain(client)
    email_s = []
    for link in links:
        parsed_data = domain.domain_search(link)
        emails = parsed_data["data"]["emails"]
        if emails:
            email = emails[0]["email"]
            email_s.append(email)

    result.append(email_s)

    return result
