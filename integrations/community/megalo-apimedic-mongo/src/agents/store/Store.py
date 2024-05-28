from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import pymongo

MONGODB_PATH = "YOUR_MONGO_CLUSTER_PATH" #example:  "mongodb://localhost:27017/"
DB_NAME = "YOUR_MONGODB_NAME"
COLL_NAME = "YOUR_DB_COLLECTION"


store_protocol = Protocol("Storing Locations")
class Hospitals(Model):
    hospitalsString : str = Field("List of hospitals that have been searched for by a user")



@store_protocol.on_message(model=Hospitals, replies = UAgentResponse)
async def on_locationReceived(ctx: Context, sender: str, msg: Hospitals):
    try:
        hospitalsJson = json.loads(msg.hospitalsString)
        client = pymongo.MongoClient(MONGODB_PATH)
        mydb = client[DB_NAME]
        mycollection = mydb[COLL_NAME]
        mycollection.insert_one(jsonRes)
     except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

    
agent.include(store_protocol)


