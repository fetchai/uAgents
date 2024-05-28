import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents import Model
from messages_helper.helper import *
# Defining classes for handling request and response

search_agent_address = "agent1qguuhg2jgvdapwadus32ym39u8crag4em4mum92gk4nz4ylgxz7ay8pqt7q"
random_agent_address = "agent1qgneem6g3tfvhpshkmfuxdgxdpvqvk9s596ff9gzf3pc3fcn942ckptq0dr"
student_agent_address = "agent1qtefvqrwcmctaaypcrpq0p7crx69gmwz7gd45rvr3u8hw095h6tdj2lcq82"

teacher_agent = Agent(
    name = 'teacher_agent',
    port = 1126,
    seed = 'teachers seed phrase',
    endpoint = 'http://localhost:1126/submit'
)

fund_agent_if_low(teacher_agent.wallet.address())


teacher_protocol = Protocol("stu Protocol")


@teacher_agent.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(teacher_agent.address)
    ctx.logger.info("teacher agent started successfully")

    option = input("Enter 1 to assign a new word to students \n enter 2 to assign test to students: ")
    
    # if option == "1":
    #     word_to_search = input("Enter the word to search: ")
    #     await ctx.send(search_agent_address, Given_word(word=word_to_search))
    if option == "1":
        await ctx.send(random_agent_address, Random_search())
    else:
        ctx.logger.info("No search requested by the teacher. Passing.")

    
@teacher_agent.on_message(model=Random_result)
async def assign_words(ctx: Context, sender: str, message: Random_result):
    word = message.word
    result = message.results
    syllables = message.syllables if message.syllables else {"blank" : "find on own :)"}
    pronunciation = message.pronunciation
    if result:
        for entry in result:
            definition = entry.get('definition', 'N/A')
            part_of_speech = entry.get('partOfSpeech', 'N/A') if entry.get('partOfSpeech', 'N/A') else "N/A"
            synonyms = ', '.join(entry.get('synonyms', [])) if entry.get('synonyms', []) else "N/A"
            type_of = ', '.join(entry.get('typeOf', [])) if entry.get('typeOf', []) else "N/A"
            examples = ', '.join(entry.get('examples', [])) if entry.get('examples', []) else "N/A"
        await ctx.send(student_agent_address, assigned_word(word=word, syllables=syllables, pronunciation=pronunciation, synonyms=synonyms, part_of_speech=part_of_speech, types_of=type_of, examples=examples))
    else:
        await ctx.send(random_agent_address, Random_search())
   
# @teacher_agent._on_startup(model=PredictionRequest, replies={PredictionResponse, Error})
# async def generate_qs(ctx: Context, sender: str, request: PredictionRequest):
    

# @teacher_agent.on_message(model=Random_result)
# async def reply_random(ctx: Context, sender: str, message: Random_result):
#     word = message.word
#     results = message.results
#     syllables = message.syllables
#     pronunciation = message.pronunciation

#     ctx.logger.info("\n\n----------------- Random Word -----------------")
#     ctx.logger.info(f"Word : {word}")
#     ctx.logger.info(f"Syllables : {syllables}")
#     ctx.logger.info(f"Pronunciation : {pronunciation}")

#     if results:
#         for entry in results:
#             definition = entry.get('definition', 'N/A')
#             part_of_speech = entry.get('partOfSpeech', 'N/A')
#             synonyms = ', '.join(entry.get('synonyms', []))
#             type_of = ', '.join(entry.get('typeOf', []))
#             examples = ', '.join(entry.get('examples', []))

#             ctx.logger.info(f"Definition: {definition}")
#             ctx.logger.info(f"Part of Speech: {part_of_speech}")
#             ctx.logger.info(f"Synonyms: {synonyms}")
#             ctx.logger.info(f"Type Of: {type_of}")
#             ctx.logger.info(f"Examples: {examples}")
#     else:
#         ctx.logger.info("No results found.")

        
if __name__ == "__main__":
    teacher_agent.run()