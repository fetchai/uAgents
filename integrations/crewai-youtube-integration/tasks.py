from textwrap import dedent
from crewai import Task

class Tasks():
    def research_youtube_content_task(self, agent, search_query, youtube_video_url=None):
        if youtube_video_url:
            description = dedent(f"""\
                Analyze the YouTube video at {youtube_video_url} for the search query: "{search_query}". Focus on extracting insights, key points, and relevant information presented in the video.
                Compile a report summarizing these insights and how they can be applied to the specific context of the job posting.""")
        else:
            description = dedent(f"""\
                Perform a general search on YouTube for the query: "{search_query}". Identify relevant videos and extract key insights, points, and information from them.
                Compile a report summarizing these insights and how they can be applied to the specific context of the job posting.""")
        
        return Task(
            description=description,
            expected_output=dedent("""\
                A comprehensive report detailing the insights, key points, and relevant information extracted from the YouTube video(s). Suggestions on incorporating these insights into the job posting should be included."""),
            agent=agent
        )
