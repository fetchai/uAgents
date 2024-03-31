# Team AN [Fetch.ai hackathon]
       BIKKI ABHIRAM,
       POOJARI NEERAJA.
       
# movie database API
project name :  CineCritique: AI-Driven Movie Reviews/download links

# description
"CineCritique: AI-Driven Movie Reviews" is a cutting-edge platform revolutionizing the way we explore and engage with films. Powered by advanced artificial intelligence algorithms, CineCritique offers comprehensive and insightful movie reviews tailored to your preferences.With CineCritique, users can delve into a vast database of films and receive personalized recommendations based on their viewing history, genre preferences, and mood. Our AI technology analyzes various aspects of each movie, including plot, direction, acting, cinematography, and more, to provide detailed and accurate critiques.Whether you're a cinephile seeking hidden gems or a casual moviegoer looking for your next weekend binge, CineCritique caters to all tastes and interests. Discover new releases, explore classic masterpieces, and uncover underrated gems with our intuitive and user-friendly interface.Experience the future of film criticism with CineCritique, where artificial intelligence meets cinematic expertise to elevate your movie-watching experience like never before.

# instructions to run the project
1.you need to check the api key.

2.install python above 3.10

3.import libraries

         [ pip install uagents]
         [ pip install transformers ]
         [ pip install ai_engine]

4. we need to create a movie details agent to get movie database and movie download url its a main task.

       [ in this agent give discription prompt that :
                                     This provides movie details and URL links to the user.
         in feild discription give the prompt that :
                                     detials:
                                                For this trigger subtask movie details.  Never ask this to user.
                                     download url:
                                                For this trigger subtask movie download links. Never ask this to user. ]

5.we need to create two sub task one is for movie details and one is for movie download url

                            [ subtask1 we can get full review of the movie details, 
                            in subtask2 we can get the torrent links to download the movie.]

# Steps to access the service/agent on DeltaV.
     
      [ - Login to [DeltaV](https://deltav.agentverse.ai/home)
        - Type in 'query' related like `I want to movie review`
        - Choose your service and provide asked details.]



# conclusion
CineCritique: AI-Driven Movie Reviews" represents a paradigm shift in the realm of film analysis and appreciation. By harnessing the power of artificial intelligence, CineCritique offers users unparalleled access to comprehensive movie critiques tailored to their individual preferences.
