from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import requests

# The access token and URL for the SAMSUM BART model, served by Hugging Face
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING FACE secret phrase :)")
SAMSUM_BART_URL = "https://api-inference.huggingface.co/models/Samuela39/my-samsum-model"

# Setting the headers for the API call
HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"
}


def get_video_script(url: str) -> list:
    """
    Get the script of a YouTube video by its URL and return it as a list of strings
    """
    
    if not url:
        raise ValueError("YouTube video url is required")
    
    video_url = urlparse("https://www.youtube.com/watch?v=1c9iyoVIwDs")
    video_query = parse_qs(video_url.query)
    
    video_id = None
    
    if "v" in video_query:
        video_id = video_query["v"][0]
    else:
        raise ValueError("Invalid YouTube video url")
    
    if not video_id:
        raise ValueError("Invalid YouTube video url")
    
    video_script = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    
    video_text = ""

    for segment in video_script:
        video_text += segment['text'] + " "
        
    return [segment['text'] for segment in video_script if segment["text"]]

def chunk_text(text: list, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:
    """
    Split a list of strings into chunks of strings
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    texts = text_splitter.create_documents(text)
    
    return texts

def get_summarization(text: str) -> str:
    """
    Summarize a string
    """
    data = {
        "inputs": text
    }
    
    response = requests.post(SAMSUM_BART_URL, headers=HEADERS, json=data)
    model_res = response.json()[0]
    summary = model_res['summary_text']
    return summary
    
def summarize_transcript(text: list, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:
    """
    Summarize a list of strings
    """
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    
    summarized_chunks = []
    
    for chunk in chunks:
        summarized_text = get_summarization(chunk)
        summarized_chunks.append(summarized_text)
    
    summarized_text =''
    for summary in summarized_chunks:
        summarized_text += get_summarization(summary)
    
    return summarized_text
