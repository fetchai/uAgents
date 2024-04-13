import google.generativeai as genai

GEMINI_API_KEY = ''
genai.configure(api_key=GEMINI_API_KEY) #replace your gemini API key here 
# Initializing the generative model with a specific model name
model = genai.GenerativeModel('gemini-pro')
        
    # Starting a new chat session
chat = model.start_chat(history=[])

def geminiOP(prompt):
        # Get user input
        user_message = 'Please summarize the following information into close to 50 words in the style of a news reporting  :  ' + prompt
            
        # Send the message to the chat session and receive a streamed response
        response = chat.send_message(user_message, stream=True)
        
        # Initialize an empty string to accumulate the response text
        full_response_text = ""
        
        # Accumulate the chunks of text
        for chunk in response:
            full_response_text += chunk.text
            
        # Print the accumulated response as a single paragraph
        message = full_response_text
        print(message)
        return message

def geminiPrompts(prompt):
    user_message = 'Please output image generation prompts for the following paragraph :  ' + prompt
        
     # Check if the user wants to quit the conversation
    if user_message.lower() == 'quit':
        return "Exiting chat session."
            
    # Send the message to the chat session and receive a streamed response
    response = chat.send_message(user_message, stream=True)
        
    # Initialize an empty string to accumulate the response text
    full_response_text = ""
        
    # Accumulate the chunks of text
    for chunk in response:
        full_response_text += chunk.text
            
    # Print the accumulated response as a single paragraph
    message = "Gemini: " + full_response_text
    print(message)
    return message