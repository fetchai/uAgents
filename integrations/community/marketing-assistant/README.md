**Title:** AI-Powered Marketing Content Generation with 
crystal-clear-xlv1, Elevenlabs, Gemini, Fetch.ai and Firebase Storage

**Description:**

This project showcases a creative integration of cutting-edge AI technologies to streamline marketing content creation for social media campaigns. It leverages the power of:

- **Crystal Clear xlv1:** A Hugging Face integration that facilitates interaction with various large language models (LLMs) like Gemini.
- **Fetch.ai AI Agent Technology:** A platform for deploying and managing intelligent agents, potentially enabling secure and decentralized content generation.

**Problem Statement:**

Marketing professionals often face the challenge of efficiently generating engaging content for social media campaigns. Manual creation is time-consuming, and traditional tools may lack the ability to produce truly unique and captivating content.

**Proposed Solution:**

This project presents a novel solution that addresses this need by providing a user-friendly service:

1. **User Input:** Users simply provide a web URL related to their campaign theme.
2. **AI-Powered Content Generation:**
   - **Web Summary:** Apyhub summarizes the provided URL, extracting key information for content direction.
   - **Post Ideas:** Gemini, an advanced LLM, generates engaging post concepts tailored to the URL's content.
   - **Reel Video Ideas:** Gemini creatively crafts video concepts to enhance the campaign's visual appeal.
   - **Image Generation:** The Crystal-Clear Stable Diffusion model, produces high-quality images that complement the generated text content.
   - **Reels Voiceover:** ElevenLabs adds a professional touch by generating voiceovers for the reel video content.
3. **Custom Integration:** Our custom code seamlessly integrates all these components, transforming text and image snapshots into compelling video content with descriptions.
4. **Storage:** Generated content (text, images, videos) is securely stored in Firebase Storage for easy access and management.
5. **Deployment:** While currently not deployed, the potential to leverage Fetch.ai's platform for deployment is explored, offering scalability and potentially secure content generation mechanisms.

**Benefits:**

- **Efficiency:** Saves time and effort compared to manual content creation.
- **Creativity:** Generates unique and engaging content ideas.
- **Scalability:** Potential for deployment on Fetch.ai facilitates handling larger workloads.
- Storage: Firebase Storage offers reliable and scalable storage for the generated content.

## Project Explanation

Google Drive Folder Link :- https://drive.google.com/drive/folders/1_pbbCpRE2KpYj20eo8n77KPlzIQ2dF4R?usp=sharing

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### Google Gemini API Key

1. Visit the Google AI Studio website: [Google AI Studio](https://makersuite.google.com/app/prompts/new_freeform)
2. Login using google credentials.
3. Click on Get API Key and store this key at safe place.
4. For more information on how to use Gemini API refer [Gemini API Quickstart](https://ai.google.dev/tutorials/python_quickstart#chat_conversations)


# Hugging Face Token

1. Visit the Hugging Face website: [https://huggingface.co/](https://huggingface.co/)
2. Sign in to your Hugging Face account or create a new one.
3. Navigate to your profile settings.
4. Find or generate your API token. If you don't have one, there is usually an option to create a new token.
5. Copy the generated token; this will be your Hugging Face Token.

# Firebase Storage Bucket, API Key, and Project ID

## Firebase Project

1. Go to the Firebase Console: [https://console.firebase.google.com/](https://console.firebase.google.com/)
2. Click on "Add project" or select an existing project.
3. Follow the on-screen instructions to set up your Firebase project.

## Firebase Storage Bucket

1. In the Firebase Console, navigate to the "Storage" section.
2. Click on "Get Started" if you haven't set up Firebase Storage yet.
3. Click on "Add a bucket" to create a new storage bucket.
4. Specify a unique name for your bucket; this will be your Firebase Storage Bucket name.

## Firebase API Key

1. In the Firebase Console, go to "Project settings" (gear icon in the left sidebar).
2. Under the "General" tab, scroll down to the "Your apps" section.
3. Find the Web App you want to use and click on the "</>" icon to get the configuration.
4. Copy the value of the `apiKey` field; this will be your Firebase API Key.

## ElevenLabs API Key

1. Visit https://elevenlabs.io/
2. Login through new id
3. Go to profile section through sidebar and copy api key.
   
## APYHUB API Key

1. Visit https://apyhub.com/
2. Login through new id
3. Go to api keys and create a new key and copy token from there.

**Disclaimer:**

This project is currently under development. The deployment on Fetch.ai is not yet implemented but is included as a potential future direction.

**Future Work:**

- **Deployment on Fetch.ai:** Explore the integration with Fetch.ai for secure and scalable content generation.
- **User Interface:** Develop a user-friendly interface for easier interaction with the service.
- **Customization:** Allow users to tailor the content generation process to their specific needs.