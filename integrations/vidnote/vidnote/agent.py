from ai_engine import UAgentResponse, UAgentResponseType
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from transformers import pipeline

AGENT_MAILBOX_KEY = "cd37caac-276f-4b7d-8748-2a0e1203863d"


whimsee_agent = Agent(
    name = "whimsee",
    seed = "video to notes",
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(whimsee_agent.wallet.address())
print(whimsee_agent.address)

class Youtubelink(Model):
    url: str


whimsee_protocol = Protocol("Video to notes converter")


async def get_video_id(url):
    # Parse the URL and extract the video ID
    path = urlparse(url).path
    if path.startswith('/shorts/'):
        video_id = path.split('/')[2]
    else:
        query = urlparse(url).query
        video_id = parse_qs(query).get('v')
        if video_id:
            video_id = video_id[0]
        else:
            raise ValueError("Invalid YouTube URL")
    return video_id

async def get_transcript(url):
    try:
        video_id = await get_video_id(url)
        # Fetch the transcript using the video ID
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        return str(e)
    

def tsummarizer(text):
    """ CONVERTS THE INPUT TEXT TO BULLET POINTED NOTES """
    print("Generating summary...")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    maxl = text.count(' ')  # total number of words is max length for summarized text
    minl = int(0.2 * maxl)  # minimum length is 20 percent of total length 
    summary = summarizer(text, min_length = minl, max_length = maxl, do_sample=False)
     
    print(summary)
    # formats the summary in bullet points.
    lines = summary[0]['summary_text'].split('.')[:-1]
    result = ''
    for point in lines:
        point = point.strip()
        result += '- ' + point + '\n'

    return result


@whimsee_protocol.on_query(model=Youtubelink, replies={UAgentResponse})
async def chunks(ctx: Context, sender: str, msg: Youtubelink):
    """ GETS THE URL --> TRANSCRIPT --> DIVIDES IT IN CHUNKS --> CONVERT TO NOTES"""

    ctx.logger.info(f'Request for video to notes conversion recieved from {sender} with url {msg.url}')
    

    transcript = await get_transcript(msg.url)

    if transcript is not None:
        print(transcript)
        ctx.logger.info("Processing the transcript...")
        tokens = transcript.split(' ')
        final_summary = 'Summary of given video url: \n'
        
        
      # divides the transcript into chunks of 1000 words and then sends it summarizer function
        for i in range(0, len(tokens), 1000):
            final_summary += tsummarizer(' '.join(tokens[i:i+1000]))
            

        await ctx.send(sender, UAgentResponse(message=str(final_summary), type=UAgentResponseType.FINAL))

    else:   #if the transcript function returns None, then User should recheck the URL
        await ctx.send(sender, UAgentResponse(message='Please check the URL and try again.', type=UAgentResponseType.ERROR))


whimsee_agent.include(whimsee_protocol, publish_manifest=True)

if __name__ == "__main__":
    whimsee_agent.run()