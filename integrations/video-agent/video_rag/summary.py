from typing import List
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
import structlog

from .utils import get_batches


summary_prompt = hub.pull("muhsinbashir/youtube-transcript-to-article")
cod_prompt = hub.pull("whiteforest/chain-of-density-prompt")


MODELS = {
    "gpt-4": "gpt-4-turbo-preview",
    "gpt-3.5": "gpt-3.5-turbo",
    "claude-3": "claude-3-opus-20240229"
}

TOKEN_LIMIT = {
    "gpt-4": 120000,
    "gpt-3.5": 12000,
    "claude-3": 190000,
}

logger = structlog.get_logger("model")


async def compress(content: str, model: str):
    # Chain inputs with defaults for all but {content}
    cod_chain_inputs = {
        'content': lambda d: d.get('content'),
        'content_category': lambda d: d.get('content_category', "Article"),
        'entity_range': lambda d: d.get('entity_range', '1-3'),
        'max_words': lambda d: int(d.get('max_words', 120)),
        'iterations': lambda d: int(d.get('iterations', 3))
    }

    model = MODELS[model]

    if model.find("gpt") != -1:
        llm = ChatOpenAI(temperature=0, model=model)
    else:
        llm = ChatAnthropic(temperature=0, model=model)

    # 1st chain, showing intermediate results, can async stream
    cod_streamable_chain = (
        cod_chain_inputs
        | cod_prompt
        | llm
        | SimpleJsonOutputParser()
    )

    cod_final_summary_chain = (
        cod_streamable_chain
        | (lambda output: output[-1].get('denser_summary', 'ERR: No "denser_summary" key in last dict'))
    )
    return await cod_final_summary_chain.ainvoke({'content': content})


async def summarize_transcript_1batch(transcript: str, model: str):
    model = MODELS[model]
    
    if model.find("gpt") != -1:
        llm = ChatOpenAI(temperature=0, model=model)
    else:
        llm = ChatAnthropic(temperature=0, model=model)

    chain = summary_prompt | llm
    article = await chain.ainvoke({"transcript": transcript})
    return article.content


merger_prompt = """
Act as an expert copywriter specializing in content optimization for SEO. Your task is to take two articles created from a YouTube transcript and transform it into a well-structured and engaging single article.
When merging the articles make sure to keep the main points and the most important information from both articles!
Keep the article structure. You can add, remove, or rewrite sentences to make the article more coherent and engaging.
Make sure you capture all the important information from both articles and make it engaging for the reader.

# ARTICLE 1
{article1}

# ARTICLE 2
{article2}
"""

async def article_merger(articles: List[str], model: str):
    if len(articles) < 2:
        return articles[0]
    
    model = MODELS[model]

    if model.find("gpt") != -1:
        llm = ChatOpenAI(temperature=0, model=model)
    else:
        llm = ChatAnthropic(temperature=0, model=model)
    
    prompt = ChatPromptTemplate.from_template(merger_prompt)

    chain = prompt | llm

    merged_article = articles[0]
    for article in articles[1:]:
        merged_article = await chain.ainvoke({"article1": merged_article, "article2": article}).content
    return merged_article


qa_prompt = """
Act as an expert question answerer. Your task is to answer the following question based on the given article.
Give a detailed and informative answer to the question.
Do your best to provide a well-structured and coherent answer. Make sure to capture all the important information from the article and make it engaging for the reader.
Also make the answer as short as possible.

# ARTICLE
{article}

# QUESTION
{question}
"""


async def answer_question(article: str, question: str, model: str):
    model = MODELS[model]

    if model.find("gpt") != -1:
        llm = ChatOpenAI(temperature=0, model=model)
    else:
        llm = ChatAnthropic(temperature=0, model=model)

    prompt = ChatPromptTemplate.from_template(qa_prompt)

    chain = prompt | llm

    answer = await chain.ainvoke({"article": article, "question": question})
    return answer.content


async def summarize_transcript(transcript: str, model: str):
    num_tokens, batches = get_batches(transcript, TOKEN_LIMIT[model])

    logger.info(f"Got transcript! Model {model}. Total token number: {num_tokens}! Number of batches: {len(batches)}")

    articles = []
    for i, batch in enumerate(batches):
        logger.info(f"Batch {i}!")
        article = await summarize_transcript_1batch(batch, model)
        articles.append(article)
    logger.info("Got articles")
    article = await article_merger(articles, model)
    logger.info("Got merged article")

    return article
