# Game Buddy

## Description
Game Buddy is a text-to-image generator program that utilizes the `ps1-graphics-sdxl-v2` model from Hugging Face to generate visual representations based on user-provided text input. The program allows users to:

- **Generate Images**: Game Buddy takes text input from the user and generates an image using the `ps1-graphics-sdxl-v2` model.
  
- **Edit Prompts/Input**: Users can edit the generated prompt or input to refine the image generation process.
  
- **Request Image Story**: Additionally, Game Buddy offers the option to provide a story related to the generated image. The story is generated using the `gemma-7b` text generation model.


## Business Model
Game Buddy can be leveraged as a service for generating custom images and associated stories based on user inputs. Potential business models include:
- **Subscription Service**: Offer different tiers of access for varying usage limits.
- **Pay-per-Use**: Charge users based on the number of image generations and story requests.
- **API Integration**: Allow other applications to integrate image and story generation as a service.

## Agents Used in our Project

### Image generation agent
- **Description**: generates images from the text input given by the user by using ps1-graphics-sdxl-v2 model.

### Customization Agent
- **Description**: Allows the user to customize their prompt .

### Story Generating Agent
- **Description**: Generates a story related to the image using gemma-7b text generation model

## Tech Stack Used
- **Python**: Programming language used for the project.
- **Hugging Face**: API used for image generation (`ps1-graphics-sdxl-v2`) and text generation (`gemma-7b`).
- **Imgur API**: Used for image hosting and retrieval.


---

## Screenshots

<img width="1440" alt="Screenshot 2024-04-13 at 11 50 58 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/e98ec35e-82af-4ced-9b90-be5685227920">

<img width="1440" alt="Screenshot 2024-04-13 at 11 51 54 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/8653ed10-6f08-497e-8706-a38bb34ea092">
<img width="1440" alt="Screenshot 2024-04-13 at 11 51 29 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/a018b595-c97f-4484-a1af-bc44bef7d488">
<img width="1440" alt="Screenshot 2024-04-13 at 11 51 18 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/ca583f2c-5f89-46d6-87fc-886bae653933">
<img width="1440" alt="Screenshot 2024-04-13 at 11 52 03 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/7573b5c4-3d7b-4b9b-819a-9afa2b42552f">
<img width="1440" alt="Screenshot 2024-04-13 at 11 52 45 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/92844621-e270-4483-be6e-ac6ca386a239">
<img width="1440" alt="Screenshot 2024-04-13 at 11 52 55 AM" src="https://github.com/Rounaknyk/uAgents/assets/90258162/fd8b49b7-aa39-4d38-9357-02f51d890854">




