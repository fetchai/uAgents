# Career Craft
## User Flow Diagram
![User Flow Diagram](https://github.com/FireFeast7/uAgents/blob/a47c3349cd3ee9617d7da5e179bbdab8b3900f8a/integrations/career-craft/images/workflow.png)
## Video Demo
Drive Links : 
1. [Resume Creation](https://drive.google.com/file/d/1cedJPCkFWvkHznjmg6EzZhquIfc5qsC2/view?usp=drive_link)
2. [Resume Optimizer](https://drive.google.com/file/d/1B37y9_t_w2iU4J5pe8bFOrut7-_UZIE_/view?usp=drive_link)
3. [Resume Analysis Matching Job Description](https://drive.google.com/file/d/1EsL0Abt31LHm2IqnXuo6LxLsthKp17QH/view?usp=drive_link)
4. [Cold Mailing to Recruiters](https://drive.google.com/file/d/1dNyU557DA7P99wNsc36lYhiow830RzJu/view?usp=drive_link)

## Mail Output

![Output](https://github.com/FireFeast7/uAgents/blob/1c070209d8d68f117351ea07bd35e6cd5d236cae/integrations/career-craft/images/ouptut.jpg)

## Abstract

Introducing a comprehensive job search tool powered by Fetch AI's uAgents. This innovative solution customises job recommendations based on your resume, helps create tailored resumes, analyses job descriptions for compatibility with your profile, and automates cold emailing with follow-up features. It revolutionises the job search process, offering personalised efficiency and seamless integration.

## Assumptions

1. It is assumed that each proposed Uagent is already deployed within the Fetch network.
2. At present, the sequence of actions among agents is pre-established. It is anticipated that DeltaV will furnish the capability to determine the most optimal arrangement of agents to effectively address the user query.
3. The selection of agents for our project aligns with the vision outlined by FetchAI.

## uAgents Proposed

- Resume Creation / Analyzer Agent

  1. **Tailored Resumes**: Craft personalised resumes based on user skills and career goals, ensuring relevance and effectiveness.

  2. **Highlight Strengths**: Identify and showcase key strengths and achievements to catch recruiters' attention.

  3. **Optimised Formatting**: Automatically format resumes for professional presentation, enhancing readability and impact.

  4. **Keyword Optimization**: Incorporate industry-specific keywords to improve ATS compatibility and increase chances of selection.

- Cold Mailing Agent

  1. **Automated Cold Emailing**: Career Craft's Cold Mailing Agent streamlines the networking process by automatically crafting personalised cold emails and messages to recruiters and hiring managers.

  2. **Time-Saving Automation**: Save valuable time and effort by eliminating the manual process of composing and sending individual cold emails. The agent handles this task efficiently, allowing users to focus on other aspects of their job search.

  3. **Personalised Messaging**: Tailor each email or message to the recipient's profile and interests, increasing the likelihood of engagement and response.

  4. **Follow-Up Features**: Built-in follow-up functionality ensures that your messages remain top of mind. The agent can automatically send follow-up emails at predefined intervals, maximising the chances of a response without requiring manual tracking.

- Job Analyzer by Resume Agent

  1. Efficient Job Matching: The Job Analyzer by Resume Agent simplifies the job search process by analysing job postings and matching them with your resume. This saves time typically spent deciphering job descriptions and ensures you focus on opportunities that align with your skills and experience.

  2. Insightful Analysis: Gain valuable insights into how well you fit each role, empowering you to tailor your application effectively. The agent provides comprehensive analysis, highlighting areas of alignment and areas for improvement to increase your chances of success.

  3. Personalised Recommendations: Receive curated job recommendations directly to your inbox based on your skills, preferences, and career aspirations. Say goodbye to endless scrolling through job boards and hello to a personalised job search experience that saves time and frustration.

## Environment Variables

Create a `.env` file and populate it with the following data:

```env
TOGETHERAI_API_KEY="your_api_key"
```

You can get the TogetherAI API from their [website](https://www.together.ai/)

## Installation

1. Clone this repository.

2. Install the required dependencies using the provided requirements.txt file:

   ```shell
   pip install -r requirements.txt
   ```

## Setup on Agentverse

1. Head over to My Agents in Agentverse and create 4 new blank Agents.

2. Update the `agent.py` file for each respective agent.

3. Create 4 services for each agent and interact with them on DeltaV.

4. For the main service, label it as "Task Service" with the 4 other services as sub-tasks, thus integrating the 4 agents.

## Contact Us

If you have any questions, suggestions, or feedback, feel free to reach out to us! We'd love to hear from you.

### Team Members

- Ameya Surana - [Email](mailto:ameyasurana10@gmail.com)
- Riya Wani - [Email](mailto:riyawani26@gmail.com)
- Mustafa Trunkwala - [Email](mailto:mustafatrunkwala8@gmail.com)
- Tejas Thorat - [Email](mailto:tejaspthorat@gmail.com)

