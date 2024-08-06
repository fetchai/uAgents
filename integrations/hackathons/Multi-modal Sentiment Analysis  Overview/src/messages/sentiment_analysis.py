# src/messages/sentiment_analysis.py
from transformers import pipeline

def analyze_sentiment(text):
    sentiment_pipeline = pipeline("sentiment-analysis")
    result = sentiment_pipeline(text)[0]
    return result
