# Food Recipe Finder

## Overview
The Food Recipe Finder enhances the capabilities of an AI agent using Python GUI, FastAPIs, Hugging Face models, and text-to-speech technology. This script allows users to upload an image of food, identifies the food item using Hugging Face's model, fetches a recipe for that food item, and displays it along with the ingredients and steps. Additionally, it provides the option to play/pause text-to-speech for the recipe steps, additional receipes for the same food and also provide keyword searching functionality.

## Usage
1. *Installation*:
    - Ensure you have Poetry installed. If not, install it using:
        ```bash
        pip install poetry```
        
2. *Install Dependencies*:
    - Run the following command to install all dependencies in a virtual environment:
        ```bash
        poetry install```
        
3. *Activate Virtual Environment*:
    - Activate the virtual environment by running:
        ```bash
        poetry shell```
        
4. *Navigate to Source Directory*:
    - Change directory to /src/agents:
        ```bash
        cd src/agents```
5. *Env Settings*:
    - create .env file and add your api keys in it
   ```API_TOKEN_higgingface="xxxxx"
    API_TOKEN_RapidAPI="xxxxx"```
    
5. *Run the Script*:
    - Execute main.py to start the Food Recipe Finder:
        ```bash
        python main.py```
        
*Note*:- If a module is found not installed please install it manually.
## Integration
You can integrate this agent into different projects by importing the run_gui function from main.py and invoking it as needed. This allows you to incorporate the Food Recipe Finder functionality seamlessly into your applications.
