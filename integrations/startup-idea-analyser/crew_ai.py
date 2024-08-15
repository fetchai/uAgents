import os

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class MarketResearchProcess:
    def __init__(self):
        api_gemini = os.environ.get("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro", verbose=True, temperature=0.1, google_api_key=api_gemini
        )

        self.marketer = Agent(
            role="Market Research Analyst",
            goal="Find out how big is the demand for my products and suggest how to reach the widest possible customer base",
            backstory="""You are an expert at understanding the market demand, target audience, and competition. This is crucial for 
                validating whether an idea fulfills a market need and has the potential to attract a wide audience. You are good at coming up
                with ideas on how to appeal to widest possible audience.
                """,
            verbose=True,  # enable more detailed or extensive output
            allow_delegation=True,  # enable collaboration between agent
            llm=self.llm,  # to load gemini
        )

        self.technologist = Agent(
            role="Technology Expert",
            goal="Make assessment on how technologically feasible the company is and what type of technologies the company needs to adopt in order to succeed",
            backstory="""You are a visionary in the realm of technology, with a deep understanding of both current and emerging technological trends. Your 
                expertise lies not just in knowing the technology but in foreseeing how it can be leveraged to solve real-world problems and drive business innovation.
                You have a knack for identifying which technological solutions best fit different business models and needs, ensuring that companies stay ahead of 
                the curve. Your insights are crucial in aligning technology with business strategies, ensuring that the technological adoption not only enhances 
                operational efficiency but also provides a competitive edge in the market.""",
            verbose=True,  # enable more detailed or extensive output
            allow_delegation=True,  # enable collaboration between agent
            llm=self.llm,  # to load gemini
        )

        self.business_consultant = Agent(
            role="Business Development Consultant",
            goal="Evaluate and advise on the business model, scalability, and potential revenue streams to ensure long-term sustainability and profitability",
            backstory="""You are a seasoned professional with expertise in shaping business strategies. Your insight is essential for turning innovative ideas 
                into viable business models. You have a keen understanding of various industries and are adept at identifying and developing potential revenue streams. 
                Your experience in scalability ensures that a business can grow without compromising its values or operational efficiency. Your advice is not just
                about immediate gains but about building a resilient and adaptable business that can thrive in a changing market.""",
            verbose=True,  # enable more detailed or extensive output
            allow_delegation=True,  # enable collaboration between agent
            llm=self.llm,  # to load gemini
        )

    def create_tasks(self, input_data):
        self.task1 = Task(
            description=f"""Analyze what the market demand for {input_data}. 
                Write a detailed report with description of what the ideal customer might look like, and how to reach the widest possible audience. The report has to 
                be concise with at least 10 bullet points and it has to address the most important areas when it comes to marketing this type of business.
            """,
            agent=self.marketer,
            expected_output="A detailed market research report with at least 10 bullet points on the ideal customer and marketing strategy.",
        )

        self.task2 = Task(
            description=f"""Analyze {input_data}. Write a detailed report 
                with description of which technologies the business needs to use in order to make High Quality T shirts. The report has to be concise with 
                at least 10 bullet points and it has to address the most important areas when it comes to manufacturing this type of business. 
            """,
            agent=self.technologist,
            expected_output="A detailed technological report with at least 10 bullet points on the necessary technologies for manufacturing.",
        )

        self.task3 = Task(
            description=f"""Analyze and summarize marketing and technological report and write a detailed business plan with 
                description of {input_data}. 
                The business plan has to be concise with at least 10 bullet points, 5 goals and it has to contain a time schedule for which goal should be achieved and when.
            """,
            agent=self.business_consultant,
            expected_output="A detailed business plan with at least 10 bullet points, 5 goals, and a time schedule.",
        )

    def run_process(self, input_data):
        self.create_tasks(input_data)

        crew = Crew(
            agents=[self.marketer, self.technologist, self.business_consultant],
            tasks=[self.task1, self.task2, self.task3],
            verbose=2,
            process=Process.sequential,  # Sequential process will have tasks executed one after the other and the outcome of the previous one is passed as extra content into this next.
        )

        result = crew.kickoff(inputs={"input": input_data})
        return result
