import paho.mqtt.client as mqtt
import random
from uagents import Agent, Context, Model,Protocol
from ai_engine import UAgentResponse, UAgentResponseType
import time
import websockets
import asyncio

argsuments={
    "endpoint": "***.amazonaws.com",
    "ca": "rootCA.pem",
    "certificate": "cert.crt",
    "key": "private.key" ,
    "pubTopic": "esp32/sub",
    "subTopic": "esp32/pub",
}

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.tls_set(
    ca_certs=argsuments["ca"],
    certfile=argsuments["certificate"],
    keyfile=argsuments["key"],
    tls_version=2)


def on_connect(mqttc, userdata, flags, rc, properties=None):
    print("connected to endpoint %s with result code %s", argsuments["endpoint"], rc)
    print("userdata: {userdata}, flags: {flags} properties: {properties}")
    mqttc.is_connected = True

# def on_message(mqttc, userdata, msg):
#     print('received message: topic: %s payload: %s', msg.topic, msg.payload.decode())
#     print("sending data to topic: %s", argsuments["pubTopic"])

def on_publish():
    print("published")


def publish():
    mqttc.loop_start()
    for i in range(2):
        print("publishing")
        mqttc.publish(argsuments["pubTopic"], "{\"message\":\"Hello form the python pub\"}",qos=0, retain=False)
        time.sleep(1)
    mqttc.loop_stop()

mqttc.on_connect = on_connect
# mqttc.on_message = on_message
mqttc.connect(argsuments["endpoint"], 8883)
# mqttc.on_publish = on_publish





simples = Protocol(name="simples", version="1.1")
class Message(Model):
    message: str


# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "something randum"

# Copy the address shown below
# print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

AGENT_MAILBOX_KEY = ""

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    publish()
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")
    


@simples.on_message(model=Message, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Message):
    
    publish()
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
 
    await ctx.send(sender, UAgentResponse(message=(f"The Result Summary:\n {msg.message} "), type=UAgentResponseType.FINAL))


agent.include(simples)



if __name__ == "__main__":
    agent.run()
