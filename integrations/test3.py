import requests
import google.generativeai as genai
# Define the GraphQL query as a multi-line string
genai.configure(api_key="AIzaSyDZbLNK62ncgJpA22-YDAaJ6gQt1CTYujE")

# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

convo = model.start_chat(history=[
])

query = '''
query (
  $page: Int,
  $perPage: Int,
  $type: MediaType,
  $sort: [MediaSort],
  $genre: String,
) {
  Page (page: $page, perPage: $perPage) {
    media (
      type: $type,
      sort: $sort,
      genre: $genre
    ) {
      id
      title {
        userPreferred
      }
      popularity
    }
  }
}
'''

# Function to get user input for media type
def get_media_type():
    while True:
        media_type = input("Enter 'anime' or 'manga' to display the list: ").strip().lower()
        if media_type in ['anime', 'manga']:
            return media_type.upper()
        else:
            print("Invalid input. Please enter 'anime' or 'manga'.")

# Function to get user input for genre
def get_genre():
    return input("Enter the genre (or leave blank for all genres): ").strip()

# Get user input for media type and genre
media_type = get_media_type()
genre = get_genre()

# Define the query variables and values based on user input
variables = {
    'page': 1,
    'perPage': 10,  # Limit to 10 results
    'type': media_type.upper(),  # Filter by user-selected media type (anime or manga)
    'sort': ['POPULARITY_DESC'],  # Sort by popularity in descending order
    'genre': genre if genre else None,  # Filter by user-selected genre (or None for all genres)
}

# Define the URL of the GraphQL API endpoint
url = 'https://graphql.anilist.co'

# Make the HTTP POST request to the API
response = requests.post(url, json={'query': query, 'variables': variables})

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Extract and print the response data
    data = response.json()
    top_10_media = data['data']['Page']['media']
    
    # Print the titles of the top 10 most popular media
    print(f"Top 10 Most Popular {media_type.capitalize()} in {genre.capitalize() if genre else 'All Genres'}:")
    for media in top_10_media:
        title = media['title']['userPreferred']
        popularity = media['popularity']
        print(f"{title} - Popularity: {popularity}")
        convo.send_message(f"write a brief description of the {title} {media_type} ")
        print(convo.last.text)
        
        
else:
    # Print an error message if the request failed
    print(f"Error: {response.status_code}")
