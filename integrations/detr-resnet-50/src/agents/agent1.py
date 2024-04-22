import streamlit as st
import threading
import requests
import tempfile
import pyttsx3  # Import pyttsx3 for text-to-speech conversion
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

# Define the API URLs and headers with your API token
DETR_API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
OBJECT_DETECTION_API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
HEADERS = {"Authorization": "Bearer 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"}

# Define the function to query the DETR model API
def query_detr(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(DETR_API_URL, headers=HEADERS, data=data)
    return response.json()

# Define the function to query the Object Detection model API
def query_object_detection(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(OBJECT_DETECTION_API_URL, headers=HEADERS, data=data)
    return response.json()

# Initialize the text-to-speech engine outside of the main function
engine = pyttsx3.init()

# Define the function to run the agent's event loop in a separate thread
def run_agent():
    alice = Agent(
    name="alice",
    port=8000,
    seed="alice secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
    )
 
    fund_agent_if_low(alice.wallet.address())
    
    @alice.on_interval(period=3)
    async def hi(ctx: Context):
        ctx.logger.info(f"Hello")
    
    alice.run()

# Start the agent's event loop in a separate thread
try:
    agent_thread = threading.Thread(target=run_agent)
    agent_thread.start()
except RuntimeError as e:
    print(f"Ignoring error: {e}")

def main():
    st.title("Image Processing")
    st.write("Upload an image to perform operations")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.write("")

        # Let the user choose between Describe Image and Object Detection options
        option = st.radio("Choose an option:", ("Describe Image", "Object Detection"))

        if option == "Describe Image":
            st.write("Describing Image...")
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            # Get the description from the Object Detection model API
            output = query_object_detection(temp_file_path)
            description = output[0].get("generated_text", "") if isinstance(output, list) and output else ""
            st.write("Description:")
            st.write(description)

            # Convert the description to audio speech
            engine.say(description)
            engine.runAndWait()

        elif option == "Object Detection":
            st.write("Detecting Objects...")
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            # Perform object detection using the DETR model API
            output = query_detr(temp_file_path)
            st.write("Object Detection Result:")
            st.write(output)

# Run the Streamlit app
if __name__ == "__main__":
    main()
