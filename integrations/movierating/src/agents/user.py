import requests

# Define the URL and headers
url = "https://moviesdatabase.p.rapidapi.com/titles/search/title/"
headers = {
    "X-RapidAPI-Key": "ca01df7077mshfea6d79a8320efdp10da96jsn10b31a2749f8",
    "X-RapidAPI-Host": "moviesdatabase.p.rapidapi.com"
}

def get_movie_id(title):
    # Construct the full URL with the title as a query parameter
    full_url = url + title.replace(" ", "%20")

    # Send a GET request to the API
    response = requests.get(full_url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Extract the movie ID if it exists
        if 'results' in data and data['results']:
            # Return the first movie ID found
            return data['results'][0]['id']
    # If something went wrong, return None
    return None
