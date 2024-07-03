from crewai import Agent
from crewai_tools.tools import YoutubeVideoSearchTool

class Agents():
    def youtube_search_agent(self, youtube_video_url=None):
        if youtube_video_url:
            tool = YoutubeVideoSearchTool(youtube_video_url=youtube_video_url)
        else:
            tool = YoutubeVideoSearchTool()
        
        return Agent(
            role='YouTube Researcher',
            goal='Analyze YouTube video content to extract insights on relevant topics.',
            tools=[tool],
            backstory='Expert in analyzing YouTube videos to identify key information and insights.',
            verbose=True
        )
