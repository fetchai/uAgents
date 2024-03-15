import os

from git import Repo
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from utils import GenericLoader, LanguageParser

OPENAI_API_KEY = "OPENAI_API_KEY"


def get_lines(repository: str, prompt: str):
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
        "Find the most relevant code for the supplied prompt along with the estimated line numbers. "
        "You will find the starting lines for each code chunk document in metadata['start_line'], "
        "so you just need to add this number to the relative position of the function in the code chunk."
        "You will find the source-file in metadata['source']."
        "Finally, attempt to compile the results as a list of github links to the code chunks in the form: "
        f"https://{repository}/blob/main/<source-file>#L<start>-L<end>."
        "It's okay if the line numbers are not perfectly accurate, just do your best to get close."
        "Prompt: " + prompt,
    ]

    result = qa.invoke(full_prompt)

    return result


if __name__ == "__main__":
    result = get_lines(
        "github.com/fetchai/uAgents/python/src/uagents",
        "Find all the functions where context appears in the code.",
    )
    print(result)
