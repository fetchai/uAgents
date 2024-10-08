import json
from urllib.parse import urljoin, urlparse

import requests
import validators
from bs4 import BeautifulSoup


def is_valid_url_format(url):
    is_valid = validators.url(url)
    if is_valid:
        return True


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def format_errors(json_input):
    data = json.loads(json_input)
    result = ""

    for item in data["errors"]:
        result += f"error: {item['error']}\nsolution: {item['solution']}\n\n"

    return result.strip()


def scrap_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        return links
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        raise Exception(f"Error accessing {url}: {e}")


def find_broken_links(url):
    broken_links = []
    invalid_links = []
    try:
        is_valid_base_url = is_valid_url_format(url=url)
        if is_valid_base_url:
            links = scrap_website(url=url)

            for link in links:
                link_url = link["href"]
                # join the URL as per host name of original URL
                full_url = urljoin(url, link_url)

                is_valid_base_url = is_valid_url_format(url=full_url)

                if not is_valid_base_url:
                    invalid_links.append(full_url)
                    continue

                if not is_valid_url(full_url):
                    invalid_links.append(full_url)
                    continue

                try:
                    link_response = requests.get(full_url)
                    if link_response.status_code == 404:
                        broken_links.append(full_url)
                except requests.exceptions.RequestException as e:
                    broken_links.append(full_url)
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        raise Exception(f"Error accessing {url}: {e}")

    return broken_links, invalid_links
