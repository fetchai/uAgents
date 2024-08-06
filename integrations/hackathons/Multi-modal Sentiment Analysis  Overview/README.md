Multi-modal Sentiment Analysis 

## Overview

This project integrates the BLIP model for image captioning with a sentiment analysis model to perform multi-modal sentiment analysis. The system is designed to analyze social media posts that include both images and text, generating captions for images and evaluating the sentiment of both the captions and accompanying text. The overall sentiment score provides a comprehensive view of the sentiment expressed in the content.

## Instructions to Run the Project

### Prerequisites

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)
- HuggingFaceAPI Token

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/akshatha-anil07/Multi-modal-Sentiment-Analysis-
   cd blip-integrations/src
   ```
   
2.  Create and Configure .env File

       Create a .env file and add your HuggingFaceAPI Token:
   ```bash
   nano .env
```
3. Add the following line to the .env file:
   ```bash
   export HUGGING_FACE_ACCESS_TOKEN="Your HuggingFaceAPI Token"
   ```
4. Load the environment variables:
    ```bash
    source .env
   ```
5. Install Dependencies

   Install the required dependencies using Poetry
```bash
poetry install
```
6. Run the Main Script

   Run the main script to perform multi-modal sentiment analysis:
```bash
poetry run python main.py
```

## Use-case Example
- Image Captioning: The generate_caption function uses the BLIP model to generate a caption for a given image.

- Sentiment Analysis: The analyze_sentiment function uses a sentiment analysis pipeline to analyze the sentiment of a given text.

- Multi-modal Integration: The main.py script integrates these two components. It generates a caption for an image, analyzes the sentiment of both the text and the caption, and then calculates an overall sentiment score.

## Example Output
When you run the main.py script, the output might look like this:
   ```text
   Generated Caption: A man holding an umbrella.
   Text Sentiment: {'label': 'POSITIVE', 'score': 0.98}
   Caption Sentiment: {'label': 'NEUTRAL', 'score': 0.50}
   Overall Sentiment: POSITIVE (Score: 0.74)
```

In this example, the system generates a caption for the image, analyzes the sentiment of the accompanying text and the generated caption, and calculates an overall sentiment score.

## Special Considerations
- API Tokens: Ensure your HuggingFaceAPI token is kept secure and not shared publicly.
- Model Performance: The quality of the generated captions and sentiment analysis might vary based on the models used and 
  the input data. It's essential to validate the performance with your specific use case.
- Environment Variables: Remember to load the environment variables from the .env file before running the script.
- Data Privacy: If analyzing real social media data, ensure compliance with data privacy regulations.


## UAgents
This project utilizes uAgents to handle the communication between the image captioning and sentiment analysis components. UAgents are lightweight agents that facilitate the interaction between different parts of the system, ensuring smooth data flow and integration.

### How UAgents are Used
- Image Captioning Agent: This agent handles the image captioning task using the BLIP model. It receives an image file path and returns the generated caption.

- Sentiment Analysis Agent: This agent handles the sentiment analysis task. It receives text (either from the generated caption or the accompanying text) and returns the sentiment analysis results.

- Coordinator Agent: This agent coordinates the entire process, invoking the image captioning agent and sentiment analysis agent as needed. It aggregates the results and calculates the overall sentiment score.


By using uAgents, the project ensures modularity and scalability, allowing each component to be developed, tested, and deployed independently.
