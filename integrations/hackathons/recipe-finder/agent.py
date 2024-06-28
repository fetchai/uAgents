# Here we demonstrate how we can create a DeltaV compatible agent responsible for generating recipes with list of
# ingredients. After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For registration,
# you will have to use the agent's address.
#
# third party modules used in this example
import requests
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


class RecipeSearch(Model):
    ingredients: str = Field(description="Describes the field where user provides the ingredients to get the recipe")


chef_agent_protocol = Protocol("Chef")


def generate_recipes_api(ingredients: list, api_key: str, num_results: int = 2) -> list:
    """Generate multiple recipes and instructions based on a single set of ingredients.

    Args:
        ingredients (list): list of ingredients.
        api_key (str): OpenAI secret key.
        num_results (integer): max number of results.
    """
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    recipes = []

    for _ in range(num_results):
        # Construct the input message for the GPT-3.5-turbo API
        prompt = f"Create a recipe using the following ingredients: {', '.join(ingredients)}."

        data = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "system", "content": "You are a helpful assistant that generates recipes."},
                         {"role": "user", "content": prompt}],
            "temperature": 0.7
        })

        try:
            response = requests.post(endpoint, headers=headers, data=data)
            response.raise_for_status()
            api_response = response.json()

            # Extract the generated message from the API response
            if api_response.get('choices'):
                recipe = api_response['choices'][0]['message']['content']
                recipes.append({"ingredients": ingredients, "recipe": recipe})
            else:
                recipes.append({"ingredients": ingredients, "recipe": None})
        except Exception as e:
            print(f"Error during OpenAI GPT-3.5-turbo API call: {e}")
            recipes.append({"ingredients": ingredients, "recipe": None})
    return recipes


@chef_agent_protocol.on_message(model=RecipeSearch, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: RecipeSearch):
    api_key = API_Key
    options = []
    splited_str = msg.ingredients.split(",")
    recipes_result = generate_recipes_api(splited_str, api_key, 2)
    for i, recipe_info in enumerate(recipes_result):
        recipe = recipe_info["recipe"]
        formatted_segment = f"""
        🌟 Instructions: {recipe}\n
    """
        options.append(formatted_segment)
    print(options)
    await ctx.send(sender, UAgentResponse(message='\n\n'.join(options), type=UAgentResponseType.FINAL))


agent.include(chef_agent_protocol)