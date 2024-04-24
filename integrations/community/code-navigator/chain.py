import os
import re

from git import Repo
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers.language import LanguageParser
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")


def find_snippet_locations(
    repository: str, repo_path: str, code_snippets: list[str], main_branch: str = "main"
) -> list[str]:
    """
    Find the files and line numbers for each of the code snippets.

    Args:
        repository (str): The repository URL.
        repo_path (str): The local repository path to search.
        code_snippets (list[str]): The code snippets to search where each snippet is in the form:
            ```{language}
            {code snippet}
            ```
            Example:
            ```python
            def foo():
                print('Hello, world!')
            ```

    Returns:
        list[str]: The snippet locations in the form of GitHub links:
            https://github.com/{repo}/blob/main/{file_path}#L{start_line}-L{end_line}
    """
    snippet_locations: list[str] = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                repo_file_path = file_path[len(repo_path) + 1 :]
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for snippet in code_snippets:
                        # extract the first 2 lines of code from the snippet:
                        snippet_lines = snippet.split("\n")[1:-1]
                        snippet_length = len(snippet_lines)
                        if snippet_length < 2:
                            pattern = re.compile(
                                r"\s*" + re.escape(snippet_lines[0]) + r"\s*"
                            )
                        else:
                            pattern = re.compile(
                                r"\s*"
                                + "\n\s*".join(
                                    [re.escape(line) for line in snippet_lines[0:2]]
                                )
                                + r"\s*",
                                re.DOTALL,
                            )

                        for match in pattern.finditer(content):
                            start_line = content.count("\n", 0, match.start()) + 1
                            end_line = start_line + snippet_length - 1
                            github_link = (
                                f"<a href=https://{repository}/blob/{main_branch}/{repo_file_path}"
                                f"#L{start_line}-L{end_line}>{repo_file_path}#L{start_line}-L{end_line}</a>"
                            )
                            snippet_locations.append(github_link)

    return snippet_locations


def extract_code_snippets_from_response(response: str) -> list[str]:
    """
    Extract the code snippets from the AI model response.

    Args:
        response (str): The AI model's response containing the code snippets.

    Returns:
        list[str]: The code snippets in the form:
            ```{language}
            {code snippet}
            ```
            Example:
            ```python
            def foo():
                print('Hello, world!')
            ```
    """
    code_snippets: list[str] = []

    snippet_start = response.find("```")
    while snippet_start != -1:
        snippet_end = response.find("```", snippet_start + 3)
        code_snippets.append(response[snippet_start : snippet_end + 3])
        snippet_start = response.find("```", snippet_end + 3)

    return code_snippets


def get_code_snippets(repository: str, prompt: str):
    repo_only = "/".join(repository.split("/")[:3])
    deeper_path = "/".join(repository.split("/")[3:])
    repo_path = "/home/james/Code/code-navigator/projects/" + repo_only.split("/")[-1]
    if not os.path.exists(repo_path):
        Repo.clone_from(f"https://{repo_only}", to_path=repo_path)

    loader = GenericLoader.from_filesystem(
        repo_path + "/" + deeper_path,
        glob="**/*",
        suffixes=[".py"],
        exclude=["**/non-utf8-encoding.py"],
        parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
    )
    documents = loader.load()

    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, chunk_size=2000, chunk_overlap=200
    )
    texts = python_splitter.split_documents(documents)

    db = Chroma.from_documents(
        texts, OpenAIEmbeddings(disallowed_special=(), api_key=OPENAI_API_KEY)
    )
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10},
    )

    llm = ChatOpenAI(model_name="gpt-4", api_key=OPENAI_API_KEY)
    memory = ConversationSummaryMemory(
        llm=llm, memory_key="chat_history", return_messages=True
    )
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, memory=memory)

    full_prompt = [
        f"""
        Your task is to find the most relevant code snippets for the query: {prompt}.
        You have been provided with a document retriever that contains all the 
        source code in the relevant repository."
        Return each code snippet in the following format: \n
        <description of the code snippet and why it is relevant> \n
        ```<language>
        <code snippet>
        ```
        For example, let's consider the prompt:
          "Find me all places where something is printed to the console."
        An appropriate response might be:
        This code snippet is relevant because "Hello, world!" is printed to the console. \n
        ```python
        def foo():
            print('Hello, world!')
        ```
        Please ensure that each code snippet is provided exactly as it appears in the source code
        without "..." or other modifications.
        """
    ]

    result = qa.invoke(full_prompt)
    response = result["answer"]

    code_snippets = extract_code_snippets_from_response(response)

    for code_snippet in code_snippets:
        snippet_locations = find_snippet_locations(
            repo_only, repo_path, [code_snippet], main_branch="main"
        )

        # Insert the snippet location just above the code snippet in the response
        if snippet_locations:
            response = response.replace(
                code_snippet,
                code_snippet
                + "\n\nGithub links:\n"
                + "\n".join(snippet_locations)
                + "\n\n",
            )

    return response


if __name__ == "__main__":
    result = get_code_snippets(
        "github.com/fetchai/uAgents/python/src/uagents",
        "Move some logic from `_process_message_queue` to `Dialogue` class",
    )
    print(result)
