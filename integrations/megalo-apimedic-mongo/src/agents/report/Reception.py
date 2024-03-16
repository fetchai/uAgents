from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field


class Listing(Model):
    spots : str = Field("List of institutions found at the location")

report_protocol = Protocol("Medical Booking System")

#Parse and load json given 
def spotsPrompt(hospitals):
    spots = ""
    ctr = 1
    for res in hospitals["resourceSets"][0]["resources"]:
        name = res["name"]
        address = res["Address"]["formattedAddress"]
        phone = res["PhoneNumber"]
        site = res["Website"]
        spots += f"{ctr}.  {name}, {address}\t{phone}\nWebsite: {site}\n\n"
        ctr+=1


#Log Ouput and pass onto Store Agent for Storing Locations
@report_protocol.on_message(model=Listing, replies = UAgentResponse)
async def on_medical_analysis(ctx: Context, sender: str, msg: Listing):
    hospitalJson = json.loads(msg.hospitals)
    prompt = spotsPrompt(hospitalJson)
    ctx.logger.info(prompts)
    await ctx.send(sender, UAgentResponse(message= str(hospitalJson), type = UAgentResponseType.FINAL))


agent.include(report_protocol)