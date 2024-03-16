import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import requests
from uagents import Agent, Context
import threading
import pyttsx3
from dotenv import load_dotenv
import os
load_dotenv()


API_TOKEN = os.getenv("API_TOKEN_huggingface")
API_URL = "https://api-inference.huggingface.co/models/nateraw/food"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Global variable to keep track of pause/play state
paused = False

def query(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

def query_recipe(para):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch"
    result = ""
    querystring = {
        "query": para,
        "addRecipeInformation": "true",
        "number": "1",
        "limitLicense": "false",
        "ranking": "2"
    }

    headers = {
        "X-RapidAPI-Key": os.getenv("API_TOKEN_RapidAPI"),
        "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()

        # Check if 'results' key exists and is not empty
        if 'results' in data and data['results']:
            recipes = data['results']
            for recipe in recipes:
                result += "Title: " + str(recipe['title']) + "\n"
                # Extract recipe ID
                recipe_id = recipe['id']
                # Use recipe ID to fetch ingredients from ingredient API
                ingredients_url = f"https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{recipe_id}/ingredientWidget.json"
                ingredients_response = requests.get(ingredients_url, headers=headers)
                if ingredients_response.status_code == 200:
                    ingredients_data = ingredients_response.json()
                    result += "Ingredients:\n"
                    for ingredient in ingredients_data['ingredients']:
                        result += "- " + str(ingredient['name']) + "\n"
                else:
                    result += "Error fetching ingredients: " + str(ingredients_response.status_code) + "\n"
                    break
                # result += "Image URL: " + str(recipe['image']) + "\n"
                if 'analyzedInstructions' in recipe:
                    instructions = recipe['analyzedInstructions']
                    for instruction in instructions:
                        steps = instruction['steps']
                        for step in steps:
                            result += "Step: " + str(step['number']) + "\n"
                            result += str(step['step']) + "\n"
                else:
                    result += "No instructions available for this recipe.\n"
        else:
            result = "No recipes found.\n"
            print("No recipes found.")
    else:
        result = "Error: " + str(response.status_code) + "\n"
        print("Error:", response.status_code)
    return result


def display_output(filename, result_text, label):
    output = query(filename)
    if output and isinstance(output, list) and len(output) > 0 and 'label' in output[0]:
        label = output[0]['label']
        response = query_recipe(label)
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, format_response(response))
        result_text.config(state=tk.DISABLED)
        
        # Speak the recipe steps
        speak_recipe(response)
    else:
        print("Error: Invalid response from API")

def speak_recipe(response):
    global paused
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    # Set voice to female
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # 1 is index for female voice
    # Loop through each line in the response and speak it
    for line in response.split('\n'):
        if paused:
            # If paused, wait until unpaused
            while paused:
                pass
        engine.say(line)
        engine.runAndWait()

def format_response(response):
    formatted_response = ""
    for section in response.split('\n'):
        if section.startswith("Title:"):
            formatted_response += f"\n\n{section}\n\n"
        elif section.startswith("Ingredients:"):
            formatted_response += f"\n{section}\n"
        elif section.startswith("Step:"):
            formatted_response += f"\n\n{section}\n"
        else:
            formatted_response += f"{section}\n"
    return formatted_response


def toggle_pause():
    global paused
    paused = not paused

def open_image(result_text, label, image_label):
    file_path = filedialog.askopenfilename()
    if file_path:
        image = Image.open(file_path)
        # Resize the image to fit within the fixed size
        image = image.resize((400, 300), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo

        # Call the API and display the output using a separate thread
        threading.Thread(target=display_output, args=(file_path, result_text, label)).start()

def run_gui():
    # Create the main window
    root = tk.Tk()
    root.title("Food Recipe Finder")  # Set window title
    root.geometry("800x400")  # Set window size

    # Create a frame to contain the image and result
    frame = tk.Frame(root)
    frame.pack(expand=True, fill="both")

    # Create a label to display the image
    image_label = tk.Label(frame)
    image_label.grid(row=0, column=0, padx=10, pady=10)

    label = tk.Label(frame)
    label.grid(row=0, column=1, padx=10, pady=10)
    
    # Create a Text widget to display the output with scrollbar
    result_text = tk.Text(frame, wrap=tk.WORD, height=10, width=50, padx=10, pady=10)
    result_text.grid(row=0, column=1, padx=10, pady=10)

    # Create a scrollbar for the result_text
    scrollbar = tk.Scrollbar(frame, command=result_text.yview)
    scrollbar.grid(row=0, column=2, sticky='ns')
    result_text.config(yscrollcommand=scrollbar.set)

    # Create a frame to contain buttons
    button_frame = tk.Frame(root)
    button_frame.pack()

    # Create "Open Image" button
    open_button = tk.Button(button_frame, text="Open Image", command=lambda: open_image(result_text, label, image_label), bg="black", fg="white", font=("Helvetica", 12, "bold"))
    open_button.pack(side="left", padx=10, pady=10)

    # Create "Pause/Play" button
    pause_play_button = tk.Button(button_frame, text="Play/Pause", command=toggle_pause, bg="black", fg="white", font=("Helvetica", 12, "bold"))
    pause_play_button.pack(side="left", padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    alice = Agent(name="alice", seed="alice recovery phrase")
    
    @alice.on_event("startup")
    def start_gui(ctx: Context):
        run_gui()

    alice.run()
