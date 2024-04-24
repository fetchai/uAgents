from uagents import Bureau


from agents.student import student_agent
from agents.search_random import word_give_agent
from agents.search_word import word_search_agent


if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    print(f"Adding agent to Bureau: {student_agent.address}")
    bureau.add(student_agent)
    print(f"Adding user agent to Bureau: {word_search_agent.address}")
    bureau.add(word_search_agent)
    print(f"Adding user agent to Bureau: {word_give_agent.address}")
    bureau.add(word_give_agent)
    bureau.run()
