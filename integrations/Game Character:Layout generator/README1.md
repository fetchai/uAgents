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

![Screenshot 1](1.jpeg)
![Screenshot 2](2.jpeg)
![Screenshot 3](3.jpeg)
![Screenshot 4](4.jpeg)
![Screenshot 5](5.jpeg)



