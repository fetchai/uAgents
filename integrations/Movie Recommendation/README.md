
# Movie Recommendation Agent 🤖

This  uAgent recommends the movies to user. It will start by showing you a variety of movies genres. Just choose the ones like action, comedy, drama, horror. Based on your selection, it will present the list of movies. when user select the movie,it will show the streaming Platform.

### Access on Agentverse [Movie Recommendation](https://agentverse.ai/agents/details/agent1qg4dmzre3rzldw67fkc4qy0r878vmzgaa0hk5g8smugnvvh65f5hqlusayf/profile)

## Usage
To start using the Movie Recommendation Agent, follow these steps:

> #### 1. Clone Repository

```bash
  git clone https://github.com/fetchai/uAgents.git
````
```bash
  cd uAgents/integrations/Movie Recommendation
````

> #### 2. Obtain API Keys - 
##### 1. TMDB
> * For Movie Database, go to [TMBD](https://developer.themoviedb.org/docs/getting-started)
> * Log in to website 
> * Create a API Keys
> * Add your API key to Code in ````utils/API.py ```` file
```javascript
TMDB_HEADER = 
    {
        "accept": "application/json",
        "Authorization": "Bearer BEARER_TOKEN"
    }
```

##### 2. Rapid API
> * Go on Rapid API [Movie Availability API](https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability/)
> * Log in to RapidAPI 
> * Subscribe to API, you will get your API KEY
> * Add your API key to Code in ````utils/API.py ```` file
```javascript
RAPID_API_HEADER = 
    {
	    "X-RapidAPI-Key": "rapid-api-key",
	    "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
    }
```

#### 4. Install Dependencies
 ```javascript
pip install -r requirements.txt
```
#### 5. Run Project - 
To run the project and its agents:
 ```javascript
python agent.py
```

## Example
````
INFO:     [ sufi]: Suggest me a good movie to watch tonight!
INFO:     [ sufi]:
0. Action.
1. Adventure.
2. Animation.
3. Comedy.
4. Crime.
5. Documentary.
6. Drama.
7. Family.
8. Fantasy.
9. History.
10. Horror.
11. Music.
12. Mystery.
13. Romance.
14. Science Fiction.
15. TV Movie.
16. Thriller.
17. War.
18. Western.

Enter Your Favourite Genres space separated :2 6 
INFO:     [bureau]: Starting server on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     [  Tom]: Received movie recommendation request from agent1qwxey9gpesal3mycqzc5ytg5jdjnk04a7pfm9kry4maxzhqu4u7c22gk9c6 with genres: ['Animation', 'Drama']
INFO:     [ sufi]: 
0. Inside Out 2.
1. Inside Out.
2. Robot Dreams.
3. The Peasants.
4. PAW Patrol: The Mighty Movie.
5. The Lion King.
6. The Lion King.
7. IF.
8. Tarzan.
9. Your Name..
10. Suzume.
11. Dragon Ball Z: Bardock - The Father of Goku.
12. Spirit: Stallion of the Cimarron.
13. The Prince of Egypt.
14. Neon Genesis Evangelion: The End of Evangelion.
15. Mary and Max.
16. The Hunchback of Notre Dame.
17. Bambi.
18. maboroshi.
19. A Silent Voice: The Movie.

Enter Index of Movie to see Where to Watch: 8
INFO:     [  Tom]: Received movie streaming  request from agent1qwxey9gpesal3mycqzc5ytg5jdjnk04a7pfm9kry4maxzhqu4u7c22gk9c6 for  Tarzan
INFO:     [ sufi]: Movie Available at
INFO:     [ sufi]:
0. Platform:prime
Link:https://www.primevideo.com/region/eu/detail/0IE8HK6UJULWS9LWKB457KSAGB/ref=atv_dp

INFO:     [ sufi]: DONE
````




## Contributors

- [@segrr](https://www.github.com/octokatherine)
- [@soham-shinde](https://github.com/soham-shinde)
- [@Anjali](https://github.com/anjalibhamare19)



