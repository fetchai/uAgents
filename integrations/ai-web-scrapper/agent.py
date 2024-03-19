import requests
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

class Summarizer(Model):
    """
    Describes the input payload.
    """
    url: str = Field(description="This field describes the url which will provided by the user")
    question: str = Field(description="This field describes the question which will also provided by the user")

def get_answer(content, question):
    try:
        api_url = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
        headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"} 
        data = {"inputs": {"question": question, "context": content}}
        
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        response_json = response.json()
        
        answer = response_json.get("answer")
        if answer:
            print(answer)
            return answer
        else:
            return "Error: Answer not found in response."
    
    except requests.RequestException as e:
        return f"Error: Request to Hugging Face API failed - {str(e)}"
    
    except ValueError as e:
        return f"Error: Failed to parse JSON response - {str(e)}"

def get_summarization(url, ctx):
    try:
        api_url = f"{HOSTED_BASE_URL}/get-summarization"
        response = requests.post(api_url, json={"url": url})
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            res_json = response.json()
            content = res_json.get("content")
            
            # Check if 'content' is present in the response JSON
            if content:
                ctx.storage.set(url, content)
                return content
            else:
                return "Error: Summarization content not found in response."
        else:
            return f"Error: HTTP status code {response.status_code} returned."

    except requests.RequestException as e:
        return f"Error: Request to API failed - {str(e)}"
    
    except ValueError as e:
        return f"Error: Failed to parse JSON response - {str(e)}"

summarizer_protocol = Protocol("Summarizer Protocol")

@summarizer_protocol.on_message(model=Summarizer, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: Summarizer):
    try:
        ctx.logger.info(msg.dict())
        content = ctx.storage.get(msg.url)
        
        # If content is not in storage, try to fetch it using get_summarization function
        scrap_content = content if content else get_summarization(msg.url, ctx)
        
        if msg.question == "":
            response = await ctx.send(sender, UAgentResponse(message=content, type=UAgentResponseType.FINAL))
            print(response)
            return
        
        answer = get_answer(scrap_content, msg.question)
        if answer:
            response = await ctx.send(sender, UAgentResponse(message=answer, type=UAgentResponseType.FINAL))
            print(response)
        else:
            await ctx.send(sender, UAgentResponse(message="No answer found!", type=UAgentResponseType.FINAL))
    
    except Exception as e:
        # Handle any unexpected exceptions
        error_message = f"An error occurred: {str(e)}"
        await ctx.send(sender, UAgentResponse(message=error_message, type=UAgentResponseType.ERROR))


agent.include(summarizer_protocol)