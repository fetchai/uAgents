## Stable Diffusion Image Generator

📌 **Overview**

Harness the power of Hugging Face's "Stable Diffusion" model with this image generator. Stable Diffusion, an avant-garde image synthesis model, seamlessly melds the capabilities of both CLIP and Diffusion techniques, churning out visually arresting images from textual descriptions. Explore the mechanics behind this innovative model [here](https://huggingface.co/CompVis/stable-diffusion-v1-4).

This system elegantly bifurcates into two agents:

1. **User Agent**: Sends forth image description requests with precision.
2. **AI Model Agent**: Skillfully interfaces with the Hugging Face API, bringing images to life.

🛠 **Requirements**

- Python (v3.10+ preferred for optimal performance)
- Poetry (A dynamic Python packaging and dependency management tool)

**Key Libraries:** Ensure your environment is configured with `HUGGING_FACE_ACCESS_TOKEN`.

✨ **Features**

- **User Agent** gracefully interacts with the AI Model Agent, firing periodic image synthesis requests.
- **AI Model Agent** efficiently retrieves images using the Stable Diffusion model, ensuring vividness and accuracy.
- Embedded error handlers diligently log and manage discrepancies, ensuring smooth operations.

## Getting Started

1. **Acquire the HuggingFaceAPI Token**:
    
    1. Visit [HuggingFace](https://huggingface.co/).
    2. Register or enter your credentials to log in.
    3. Chart a course to `Profile -> Settings -> Access Tokens`.
    4. Copy an existing token or mint a new one.

2. **Environment Setup**: Within the `stable_diffusion-v1-4/src` directory, forge a `.env` file and inscribe your HuggingFaceAPI Token:

    ```bash
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    ```

3. **Install Dependencies**:

    Venture into the source directory, load the environment variables from `.env`, and install necessary packages:

    ```bash
    cd src
    source .env
    poetry install
    ```

4. **Ignite the Main Script**:

    Kickstart the project using:

    ```bash
    poetry run python main.py
    ```

This sequence dispatches requests to the agent at 10-minute intervals.

In your logs, scout for:

```
Adding agent to Bureau: {agent_address}
```

Snatch the {agent_address} value and transpose `AI_MODEL_AGENT_ADDRESS` in `src/stable_diffusion_agent.py` with this value.

Wish to tailor your request? Navigate to `src/stable_diffusion_user.py` and tweak the `IMAGE_DESC` variable to customize the textual prompt.

Your freshly minted images reside in the `generated-image` folder. Named with a timestamp, for instance: **2023-09-03 11:00:59.jpeg**.

Dive in and conjure some mesmerizing visuals!