# Startup Idea Analyser

Ever had that brilliant startup idea flash through your mind? Whether it's over morning coffee or during your daily commute, we've all dreamt of turning those sparks into successful ventures. Taking that first step can seem daunting. That's why I've harnessed the power of Fetch.AI agent and Crew AI agent technology to develop a multi-agent integration, designed to transform your budding ideas into solid, actionable business plans.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

**Startup Idea Analyser** is an innovative tool that leverages Fetch.AI's agent technology to assist budding entrepreneurs in transforming their startup ideas into comprehensive business plans. This system integrates multiple agents to provide market research, technological analysis, and business strategy development, ultimately delivering a detailed roadmap to success.

## Features

- **Market Research**: The Marketing Agent dives deep into understanding the demand for your product, defining the ideal customer, and crafting strategies to reach a wide audience.
- **Technological Analysis**: The Technology Expert Agent assesses essential technologies needed to create your product efficiently and with top quality.
- **Business Strategy Development**: The Business Consultant Agent synthesizes the information into a comprehensive business plan. This plan includes key strategies, detailed milestones, and a timeline to guide you toward profitability and sustainability.
- Provides over 10 crucial insights
- Identifies 5 clear business goals
- Generates a detailed timeline charting your path to success

## How It Works

Imagine a system that not only aids in market analysis and technology assessment but also provides you with a tailor-made business blueprint for success. Here's how it works:

1. **Market Research**: The Marketing Agent conducts thorough research to understand market demand, customer demographics, and effective marketing strategies.
2. **Technological Analysis**: The Technology Expert Agent evaluates the necessary technologies, offering insights on the best tools and methods for your product development.
3. **Business Strategy Development**: The Business Consultant Agent consolidates all gathered information to create a comprehensive business plan, including strategies, milestones, and a timeline.

## Installation

To get started with **Startup Idea Analyser**, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fetchai/uAgents.git
   cd startup-idea-analyser

2. **Set up .env file**:
   To run the demo, you need to add these API keys in .env file:
   ```bash
   AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

3. **Open a shell**:
   ```bash
   poetry shell

4. **Install dependencies using Poetry**:
   ```bash
   poetry install --no-root

5. **Run the agent**:
   ```bash
   poetry run python agent.py
