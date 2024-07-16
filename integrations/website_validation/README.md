# Website Validation

Ensuring the accuracy and functionality of your website is crucial for maintaining a professional online presence. Whether you're a business owner, a developer, or a content creator, having a tool that can efficiently validate your website is invaluable. That's why I've harnessed the power of Crew AI agent technology to develop a comprehensive website validation tool.

## Introduction

**Website Validator** is an innovative tool that leverages Crew AI agent technology to ensure your website is error-free and fully functional. This system checks for typos and identifies broken or invalid links, providing a detailed report to help you maintain a high-quality website.

## Features

- **Typo Detection**: The CrewAI agent scans your website content to identify and suggest corrections for any typos.
- **Broken Link Detection**: The tool checks for broken or invalid links throughout your website, ensuring all links are functional.
- **Comprehensive Reporting**: Receive detailed reports highlighting typos and broken links, allowing you to address issues promptly.

## How It Works

The Website Validator works through a seamless process to ensure your website is in top condition:

1. **Input Website URL**: Enter the URL of the website you want to validate.
2. **Check for Broken Links**: The tool first scans the website for any broken or invalid links, ensuring all hyperlinks are functional.
3. **Scrape Website Data**: The tool scrapes the website content to prepare it for typo detection.
4. **Typo Detection**: The CrewAI agent analyzes the scraped data to identify and suggest corrections for any typos.

## Installation

To get started with **Startup Idea Analyser**, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fetchai/uAgents.git
   cd website_validation

2. **Set up .env file**:
   To run the demo, you need to add these API keys in .env file:
   ```bash
   AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"
   OPEN_AI_BASE_URL="YOUR_OPEN_AI_BASE_URL"
   OPEN_AI_API_KEY="YOUR_OPEN_AI_BASE_KEY"
   OPEN_AI_MODEL_NAME="YOUR_OPEN_AI_MODEL_NAME"
3. **Open a shell**:
   ```bash
   poetry shell

4. **Install dependencies using Poetry**:
   ```bash
   poetry install --no-root
5. **Run the agent**:
   ```bash
   poetry run python agent.py