## TherapEaseAI

This project is is part of the Fetch.ai hackathon submission at NIT Goa. We were given a Hugging Face model - [_t5-base-finetuned-emotion_](https://huggingface.co/mrm8488/t5-base-finetuned-emotion) (text-to-text model) to use the model to detect emotions in conversations.

![ENV file](docs/main.png)

### 🏆 Our Goal

We aimed to make use of the given Hugging Face Model for Emotion Recognition combined with Gemini API to build a mental health therapy platform. This platform is powered by two micro-agents implemented using the the uagents library.

### 🔗 ToC

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Environment Variables](#-environment-variables)
- [Run Locally](#-run-locally)
- [Documentation](#-documentation)
- [Demo](#-demo)
- [Whatsapp Demo](#whatsapp-demo)
- [Screenshots](#screenshots)
- [Team](#-team)

### 📋 Features

- **USER'S Mental Health Assessment :** We are analysing our user's mental health dynamically while he/she is chatting with our AI Agent. After a conversation we give a detailed mental health assessment report to the user based on the detected emotions and problems.

- **Mental Health Therapist Reccomendation :** If the user's assessment report shows signs of depression, anxiety or any other mental health issues that are SEVERE then we reccomend top 5 mental health therapists based on user's location.

- **Mental Health Resources :** We provide a list of mental health resources like helplines, websites,videos and support groups to the user based on their location for users having MILD symptoms.

- **Dedicated WhatsApp Bot :** We have also built the same AI Chatbot on WhatsApp platform using the WhatApp Cloud APIs and Custom Webhooks. So users can also chat with our AI therapist on WhatsApp for 24/7 support.

### 🧰 Tech Stack

- **Libraries Used** : uAgents, Flask, Langchain, Google-generativeai, transformers _(Python)_

- **Hugging Face API**: [t5-base-finetuned-emotion](https://huggingface.co/mrm8488/t5-base-finetuned-emotion)

### 🔐 Environment Variables

To run this project, you will need to add the following environment variables to your **.env** file

- `ACCESS_TOKEN` - Enter_your_whats_app_access_token

- `APP_ID` - enter_your_whats_app_app_id

- `APP_SECRET` - enter_your_whats_app_app_secret

- `RECIPIENT_WAID`- enter_your_whats_app_message_recipiant_number
- `VERSION` - whats_app_graph_api_version
- `PHONE_NUMBER_ID` - enter_whats_app_test_phone_number
- `VERIFY_TOKEN`- enter_your_whats_app_verificaiton_token
- `GEMINI_API_KEY` - enter_your_gemini_access_key

![ENV file](docs/env.png)

### 💻 Local Setup

**_Step#1 : Clone Project Repository_**

```bash
git clone https://github.com/Pixathon-Saavyas/Gamma-Rays.git
```

**_Step#2 : Create Virtual Environment_**

- If _virtualenv_ is not istalled :

```bash
pip install virtualenv && virtualenv env
```

- **In Windows :**

```bash
env/Scripts/activate
```

- **In Linux or MacOS :**

```bash
source env/bin/activate
```

**_Step#3 : Install Dependencies_**

```bash
pip install --upgrade pip -r requirements.txt
```

**_Step#4 : Add .env file_**

- ENV file contents
  - **In Windows :**
  ```bash
      copy .env.example .env
  ```
  - **In Linux or MacOS :**
  ```bash
      cp .env.example .env
  ```
- Enter Your Credentials in the _".env"_ file. Refer [Environment Variables](#-environment-variables)

**_Step#5 : [FOR CLI DEMO] Run the agents in the terminal and start interacting_**

```bash
python two_agents.py
```

**_Step#6 : [FOR WHATSAPP DEMO] Run the following commands:_**

```bash
cd server
```

```bash
python run.py
```

```bash
ngrok http 8000 --domain accurately-frank-wombat.ngrok-free.app
```

_Check the terminal if any error._

### 📄 Documentation

The docs folder contain all the project documentations and screenshots of the project.

- **Local Server Base Link :** http://localhost:8000/

- **Ngroc Server Link (Not Permament) :** https://accurately-frank-wombat.ngrok-free.app

### 🧑🏻‍💻 Demo

- CLI Demo Link: https://youtu.be/3N4rVFrFyrI

### 🤳 Whatsapp Demo

We implemented the agents and integrate it into the Whatsapp API. This is a long form chat version, where the user can interact with agent with more than 1 message, after which a detailed analysis of the conversation is done. This analysis leads to the user being suggested a list of therapists he can approach.

> Demo Link: https://youtu.be/9Ec6OQ3AgxY

![ENV file](docs/whatsapp.png)

## 📸 Screenshots

![alt text](image.png)

> DeltaV platform

### 👨‍👦‍👦 Team

- `Pratham Shankhwalker` - _Python_ - [LinkedIn](https://www.linkedin.com/in/pratham-shankwalker-ab2899205/), [GitHub](https://github.com/prathamshankwalker) - Machine Learning (ML) Developer

- `Atharva Parkhe` - _Python_ - [LinkedIn](https://www.linkedin.com/in/atharva-parkhe-3283b2202/), [GitHub](https://github.com/atharvparkhe), [Instagram](https://www.instagram.com/atharvparkhe/) - Backend Developer

- `Medam Greeshma` - _JavaScript_ - [LinkedIn](https://www.linkedin.com/in/m-greeshma/), [GitHub](https://github.com/Greeshma2903) - Frontend Developer
