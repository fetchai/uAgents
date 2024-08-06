# src/main.py
from utils.utility_x import perform_sentiment_analysis

IMAGE_FILE = "images/your_image.jpg"
TEXT = "This is a sample text accompanying the image."

def main():
    results = perform_sentiment_analysis(IMAGE_FILE, TEXT)
    print(f"Generated Caption: {results['caption']}")
    print(f"Text Sentiment: {results['text_sentiment']}")
    print(f"Caption Sentiment: {results['caption_sentiment']}")
    print(f"Overall Sentiment: {results['overall_sentiment']} (Score: {results['overall_score']})")

if __name__ == "__main__":
    main()
