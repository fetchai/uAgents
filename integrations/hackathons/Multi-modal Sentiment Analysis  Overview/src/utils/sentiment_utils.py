# src/utils/sentiment_utils.py
import os
from agents import generate_caption
from messages import analyze_sentiment

def perform_sentiment_analysis(image_path, text):
    caption = generate_caption(image_path)
    text_sentiment = analyze_sentiment(text)
    caption_sentiment = analyze_sentiment(caption)

    overall_sentiment_score = (text_sentiment['score'] + caption_sentiment['score']) / 2
    overall_sentiment_label = "POSITIVE" if overall_sentiment_score > 0.5 else "NEGATIVE"

    return {
        "caption": caption,
        "text_sentiment": text_sentiment,
        "caption_sentiment": caption_sentiment,
        "overall_sentiment": overall_sentiment_label,
        "overall_score": overall_sentiment_score
    }
