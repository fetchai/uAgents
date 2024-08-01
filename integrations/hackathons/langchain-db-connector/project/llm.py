"""
langchain specific code
"""

from operator import itemgetter

from dotenv import load_dotenv
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


class Database:
    def __init__(self, host, name, description):
        self.host = host
        self.name = name
        self.description = description
        self.db = SQLDatabase.from_uri(host)


databases: list[Database] = []


def init_db_objects(host: str, name: str, description: str) -> None:
    """Database initialization with langchain compatible objects."""
    databases.append(Database(host, name, description))


def get_db_by_prompt(prompt: str) -> str:
    """
    Function to infer the desired database name from the prompt.

    prompt -> LLM -> database name
    """

    descriptions = [
        f"This database is called {db.name} in lowercase. " + db.description
        for db in databases
    ]

    vectorstore = FAISS.from_texts(descriptions, embedding=OpenAIEmbeddings())
    retriever = vectorstore.as_retriever()

    template = """Answer the question based only on the following context:
            {context}.
            Do only use the name of the database to answer the question.
            Don't use a sentence or a paragraph.
            If you don't find a proper answer, you can answer with "".

            Question: {question}
            """
    template_prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | template_prompt
        | llm
        | StrOutputParser()
    )
    return chain.invoke(prompt)


def query_langchain(prompt: str) -> str:
    """
    Main function to generate the query for the database.

    prompt -> LLM -> SQL query -> SQL result -> LLM -> answer
    """

    db = databases[0].db  # default to first database

    if len(databases) > 1:
        my_db = get_db_by_prompt(prompt)
        if my_db:
            db = [x.db for x in databases if x.name == my_db][0]

    execute_query = QuerySQLDataBaseTool(db=db)
    write_query = create_sql_query_chain(llm, db)

    answer_prompt = PromptTemplate.from_template(
        """Given the following user question about the database,
        corresponding SQL query, and SQL result, answer the user question.
        If the user question is asking about "you" or "your", then answer
        the question as if you are the database.

        Question: {question}
        SQL Query: {query}
        SQL Result: {result}
        Answer: """
    )

    chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query
        )
        | answer_prompt
        | llm
        | StrOutputParser()
    )
    return chain.invoke({"question": prompt})
