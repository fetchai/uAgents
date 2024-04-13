from uagents import Agent, Context, Model
from imgtopdf import convert_images_to_pdf
from prompt2image import save_images_from_query
from prompt import generate_summary
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

class Message(Model):
    text: str

# Folder to store images
image_folder = "images"
# Text file to store prompts
text_file = "text_file.txt"
# Path to the generated PDF file
pdf_path = "all_images_with_text.pdf"

# Generate a secure seed phrase
SEED_PHRASE = os.getenv("SEED_PHRASE")

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

@agent.on_message(model=Message)
async def handle_story(ctx: Context, sender: str, msg: Message):
    # Log the received story
    ctx.logger.info(f"Received story from {sender}: {msg.text}")
    
    # Generate summary for the received story
    generated_summary = generate_summary(msg.text)
    
    # Split the summary into parts
    parts = generated_summary.split("[&&&]")
    
    # Process each part
    for i, part in enumerate(parts, 1):
        try:
            # Generate summary for the part
            part_summary = generate_summary(part)
            
            # Save images from the generated summary
            save_images_from_query(part_summary, folder='images', filename_prefix=f'part_{i}_image')
            
            # Check if it's the last prompt
            if i == len(parts):
                break
        except Exception as e:
            # Log any errors that occur during processing
            ctx.logger.error(f"An error occurred while processing part {i}: {e}")
            break
    
    # Convert the saved images to PDF with associated prompts
    convert_images_to_pdf(image_folder, text_file, pdf_path)

# Run the agent
if __name__ == "__main__":
    agent.run()
