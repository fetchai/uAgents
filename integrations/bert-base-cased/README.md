# 🤖 BERT Base Cased Integration

Integrate the BERT (Masked Language Model) to predict masked words using the cased model, seamlessly integrated with uAgent.
BERT is a transformers model pretrained on a large corpus of English data in a self-supervised fashion. This means it was pretrained on the raw texts only, with no humans labeling them in any way (which is why it can use lots of publicly available data) with an automatic process to generate inputs and labels from those texts.
This model is cased: it does make a difference between english and English.

![BERT Logo](https://path/to/bert-logo.png)

## 🛠️ Prerequisites

Before getting started, make sure you have the following software installed:

- Python (v3.10+ recommended)
- Poetry (a Python packaging and dependency management tool)

## 🚀 Setup

1. **Obtain HuggingFace API Token:**

    - Visit [HuggingFace](https://huggingface.co/).
    - Sign up or log in.
    - Navigate to `Profile -> Settings -> Access Tokens`.
    - Copy an existing token or create a new one.

2. **Configure Environment:**

    - Set your HuggingFace API Token as follows:

        ```
        export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFace API Token}"
        ```

3. **Install Dependencies:**

    ```bash
    poetry install
    ```

## 📋 Running The Script

To run the project, use the following command:

```
poetry run python main.py
```

You can change the input text to whatever you like. Open the `src/bert_base_user.py` file and modify the value of the `INPUT_TEXT` variable in `agents/bert_base_user.py`.

The BERT Base model will suggest the most appropriate word to be replaced.
