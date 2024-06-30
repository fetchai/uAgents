# Hire AI Influencer 
#### Hire AI influencer for your brand collaboration directly from Delta V. ✨
> instant posts to your chosen model.
 
> built using fetch.ai's uagents technology

> user asks to hire ai influencer, gets the option to choose from the avaiable models. User can then provide brand prompt to be uploaded to the indluncer's account.
> 
### NOTE: Put the API keys in config.json and for Firebase please refer to the video given.
## AI Model Creation from Prompt
This repository demonstrates creating an AI model from a prompt using Stable Diffusion.

## Usage Clone the Repository

bash Copy code git clone 
```
git clone https://github.com/saquib000/fetchai-hack.git
cd fetchai-hack
```
Set Up a Virtual Environment
bash Copy code 
```
python3 -m venv venv
source venv/bin/activate
# On Windows, use
venv\Scripts\activate Install Dependencies
```

Install requirements now
```
pip install -r requirements.txt 
```

## Generate AI Model from Prompt

python Copy code from stable_diffusion import StableDiffusion

## Initialize the Stable Diffusion model
```
model = StableDiffusion()
## Define your text prompt
text_prompt = "A powerful AI model capable of understanding complex tasks."

## Generate the AI model
ai_model = model.create_model(text_prompt)

## Save the AI model
ai_model.save("output/ai_model.pth") Use the Generated AI Model
```
Once the AI model is generated, you can use it for various tasks such as natural language processing, image recognition, or any other task depending on the prompt provided.


## Setting Up Firebase Cloud
Firebase Cloud provides a powerful platform for developing and deploying web and mobile applications. Follow these instructions to set up Firebase Cloud for your project:

1. Download serviceAccount.json
2. Log in to your Firebase console.
3. Navigate to your project settings.
4. Go to the "Service accounts" tab.
5. Click on "Generate new private key".
6. Save the downloaded JSON file as serviceAccount.json in your project directory.
Add Required Configurations

### Setup Firebase:


Refer to Video Tutorial

Check out this video tutorial for a visual guide on setting up Firebase Cloud: https://www.youtube.com/watch?v=f388UfOoF4g

Firebase Cloud Setup Tutorial

This tutorial will guide you through the setup process step by step, ensuring you have all the necessary configurations in place.

Once you've completed these steps, you'll have Firebase Cloud set up and ready to use for your project. Make sure to refer to the Firebase documentation for detailed information on utilizing Firebase services for your specific application needs.

### Contributing Contributions are welcome! If you'd like to contribute, please follow these steps:

### 1. Fork the repository. Create a new branch (git checkout -b feature-branch). 
### 2. Make your changes. Commit your changes (git commit -m 'Add some feature'). 
### 3. Push to the branch (git push origin feature-branch). 
### 4. Open a Pull Request. 

### DeltaV chat screenshots
![App Screenshot](https://github.com/saquib000/fetchai-hack/blob/main/screenshots/deltav.jpeg)
![App Screenshot](https://github.com/saquib000/fetchai-hack/blob/main/screenshots/deltav2.jpeg)
### AI Influencer's socials : auto upload of prompt generated image
<img width="1280" alt="Screenshot 2024-06-09 at 4 17 43 PM" src="https://github.com/saquib000/uAgents/assets/103306537/a46aeca1-4632-4106-920e-eaf24153b7a8">
<img width="1280" alt="Screenshot 2024-06-09 at 4 18 11 PM" src="https://github.com/saquib000/uAgents/assets/103306537/c42ed528-b4c5-46c7-b837-28319dabaec1">




