# Top 5 Priority Emails Agent

## **About Top 5 Priority Emails**

The Top 5 Priority Emails agent allows users to connect their email account and get the top 5 priority emails. The agent uses openAI GPT-3.5 to understand the urgency of emails, so you never miss an important deadline or opportunity

## Requirements

- Python (v3.10+ recommended)
- Poetry

## Setup

1. For the demo to work, you need to:

    1. Visit [Google App Passwords](https://myaccount.google.com/apppasswords).
    2. Sign up or log in.
    3. Create an app password (that will be the new password for the agent to access your email account).
    4. Get a new OpenAI API key from [OpenAI](https://platform.openai.com/playground).


## How to Use

To leverage the Top 5 Priority Emails Agent through DeltaV, follow these simple steps:

1. **Access DeltaV**:
   - Go to [DeltaV](https://deltav.agentverse.ai/).
   - Select the "All Service Group."
2. **Initiate a Request**:
   - Use the prompt: "Get my top 5 priority emails."
3. **Provide Required Information**:
   - **Email/Password**: Enter your email and the app password you created. 

The agent will then use the OpenAI GPT-3.5 model to understand the urgency of the emails and return the top 5 priority emails.

## Libraries Used

This service incorporates several key libraries to provide its functionality:

- **fetch-uagents**
- **langchain**
- **GPT-3.5**
