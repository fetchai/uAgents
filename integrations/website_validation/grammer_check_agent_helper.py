import os
from textwrap import dedent

import requests
from bs4 import BeautifulSoup
from crewai import Agent as CrewAgent
from crewai import Task
from dotenv import load_dotenv
from langchain.chat_models.openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

# CrewAI Logic
default_llm = ChatOpenAI(
    openai_api_base=os.getenv("OPEN_AI_BASE_URL"),
    openai_api_key=os.getenv("OPEN_AI_API_KEY"),
    temperature=0.1,
    model_name=os.getenv("OPEN_AI_MODEL_NAME"),
)


# models to llm response format
class GrammarMistakes(BaseModel):
    """Campaign idea model"""

    error: str = Field(..., description="error/mistake in content")
    solution: str = Field(..., description="solution to that error")


class Mistakes(BaseModel):
    errors: list[GrammarMistakes]


def scrape_website(url):
    """
    Scrapes the specified website and returns the text content.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses

        soup = BeautifulSoup(response.text, "html.parser")

        webiste_content = []

        for script in soup(["script", "style"]):
            script.decompose()

        def print_leaf_text(element):
            if not element.find_all():
                # Check if the element is a leaf node (no children)
                content = element.get_text(separator="\n").strip()
                if content:
                    webiste_content.append(content)
            else:
                for child in element.find_all(recursive=False):
                    # Recur for each child element
                    print_leaf_text(child)

        _ = print_leaf_text(soup)
        return webiste_content
    except Exception as e:
        print(f"Exception while scrapping {url}. error: {e}")
        raise Exception(e)


def find_content_grammar_mistakes(content):
    """
    get the scrapped content and return the grammar mistakes with suggested solution.
    """
    try:
        grammar_analyzer_agent = CrewAgent(
            role="Quality Assurance Editor",
            goal=f"""Identify and correct grammatical mistakes in provided content. 
                Prioritize sentences first and then words. Provide all errors 
                and suggested solutions in a key-value pair format, where the key 
                is the wrong statement or word (error) and the value is its 
                respective solution.
                """,
            backstory="""You are a meticulous Quality Assurance Editor with a sharp 
                    eye for detail and a passion for linguistic precision. Your 
                    expertise lies in reviewing, refining, and perfecting content 
                    to ensure it adheres to the highest standards of grammar, style, 
                    and coherence. You excel in identifying and correcting 
                    grammatical errors, inconsistencies, and stylistic deviations 
                    across various types of written material.""",
            llm=default_llm,
        )

        grammar_review_task = Task(
            description=f"""Grammar Mistakes finder and suggest solution to those mistakes.""",
            agent=grammar_analyzer_agent,
            expected_output=dedent(
                f"""
                    give me list of grammar mistakes available in given content(list of words/sentence): {content}
                    result should follow belowed mentioned pydantic model and make sure to not repeat sentence or word:
                    
                    class GrammarMistakes(BaseModel):
                        error: str = Field(..., description="error/mistake in content")
                        solution: str = Field(..., description="solution to that error")


                    class Mistakes(BaseModel):
                        errors: list[GrammarMistakes]
                    """
            ),
            output_json=Mistakes,
        )
        results = grammar_review_task.execute()
        return results
    except Exception as e:
        print(f"Exception while finding grammar mistakes {e}")
        raise Exception(e)
