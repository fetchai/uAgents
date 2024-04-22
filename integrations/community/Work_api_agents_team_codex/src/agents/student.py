import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents import Model
from messages_helper.helper import *
# Defining classes for handling request and response

search_agent_address = "agent1qguuhg2jgvdapwadus32ym39u8crag4em4mum92gk4nz4ylgxz7ay8pqt7q"
random_agent_address = "agent1qgneem6g3tfvhpshkmfuxdgxdpvqvk9s596ff9gzf3pc3fcn942ckptq0dr"

student_agent = Agent(
    name = 'student_agent',
    port = 1125,
    seed = 'stu seed phrase',
    endpoint = 'http://localhost:1125/submit'
)

fund_agent_if_low(student_agent.wallet.address())


student_protocol = Protocol("stu Protocol")



@student_agent.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info("Student agent started successfully")
    # await ctx.send()
    option = input("Enter 'search' to search for a new word or enter 'random' for a random word: ")
    
    
    if option == "search":
        word_to_search = input("Enter the word to search: ")
        await ctx.send(search_agent_address, Given_word(word=word_to_search))
    elif option == "random":
        await ctx.send(random_agent_address, Random_search())
    else:
        ctx.logger.info("No search requested by the student. Passing.")
# @student_agent.on_event('startup')

# async def meaning(ctx:Context,sender:str,message=Request):
#     word = input("Enter the word to get meaning: ")
#     await ctx.send(search_agent_address, Request(text=word))
    
get_assigned_word = False
@student_agent.on_message(model=assigned_word)
async def get_word(ctx: Context, sender: str, message: assigned_word):
    global get_assigned_word
    word = message.word
    syllables = message.syllables
    pronunciation = message.pronunciation
    synonyms = message.synonyms
    part_of_speech = message.part_of_speech
    types_of = message.types_of
    examples = message.examples
    ctx.logger.info("saving this word to storage.")
    ctx.storage.set("word", word)
    
    
    ctx.logger.info("\n\n----------------- Assigned Word -----------------")
    ctx.logger.info(f"Word : {word}")
    ctx.logger.info(f"Syllables : {syllables}")
    ctx.logger.info(f"Pronunciation : {pronunciation}")
    ctx.logger.info(f"Synonyms : {synonyms}")
    ctx.logger.info(f"Part of Speech : {part_of_speech}")
    ctx.logger.info(f"Types of : {types_of}")
    ctx.logger.info(f"Examples : {examples}")
    get_assigned_word = True
    
    
@student_agent.on_message(model=Result)
async def reply_sir(ctx: Context, sender: str, message: Result):
    word = message.word
    result = message.result
    syllables = message.syllables
    pronunciation = message.pronunciation

    ctx.logger.info("\n\n----------------- Given Word -----------------")
    ctx.logger.info(f"Word : {word}")
    ctx.logger.info(f"Syllables : {syllables}")
    ctx.logger.info(f"Pronunciation : {pronunciation}")

    if result:
        for entry in result:
            definition = entry.get('definition', 'N/A')
            part_of_speech = entry.get('partOfSpeech', 'N/A')
            synonyms = ', '.join(entry.get('synonyms', []))
            type_of = ', '.join(entry.get('typeOf', []))
            examples = ', '.join(entry.get('examples', []))

            ctx.logger.info(f"Definition: {definition}")
            ctx.logger.info(f"Part of Speech: {part_of_speech}")
            ctx.logger.info(f"Synonyms: {synonyms}")
            ctx.logger.info(f"Type Of: {type_of}")
            ctx.logger.info(f"Examples: {examples}")
    else:
        ctx.logger.info("No results found.")

@student_agent.on_message(model=Random_result)
async def reply_random(ctx: Context, sender: str, message: Random_result):
    word = message.word
    results = message.results
    syllables = message.syllables
    pronunciation = message.pronunciation

    ctx.logger.info("\n\n----------------- Random Word -----------------")
    ctx.logger.info(f"Word : {word}")
    ctx.logger.info(f"Syllables : {syllables}")
    ctx.logger.info(f"Pronunciation : {pronunciation}")

    if results:
        for entry in results:
            definition = entry.get('definition', 'N/A')
            part_of_speech = entry.get('partOfSpeech', 'N/A')
            synonyms = ', '.join(entry.get('synonyms', []))
            type_of = ', '.join(entry.get('typeOf', []))
            examples = ', '.join(entry.get('examples', []))

            ctx.logger.info(f"Definition: {definition}")
            ctx.logger.info(f"Part of Speech: {part_of_speech}")
            ctx.logger.info(f"Synonyms: {synonyms}")
            ctx.logger.info(f"Type Of: {type_of}")
            ctx.logger.info(f"Examples: {examples}")
    else:
        ctx.logger.info("No results found.")



        
if __name__ == "__main__":
    student_agent.run()