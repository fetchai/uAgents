import paho.mqtt.client as mqtt
import random
from uagents import Agent, Context, Model,Protocol



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

def pub_and_sub():
    mqttc.publish(argsuments["pubTopic"], "{\"message\":\"Hello World\"}")


def on_connect(mqttc, userdata, flags, rc, properties=None):
    global TOPIC_ALIAS_MAX
    print("connected to endpoint %s with result code %s", argsuments["endpoint"], rc)
    print("userdata: %s, flags: %s properties: %s", userdata, flags, properties)
    # print("topic_alias_maximum: %s", properties.TopicAliasMaximum)
    # TOPIC_ALIAS_MAX = properties.TopicAliasMaximum
    mqttc.is_connected = True

    print('subscribing to topic: %s', argsuments["subTopic"])
    mqttc.subscribe(argsuments["subTopic"], qos=0, options=None, properties=None)
    # topic_alias = random.SystemRandom().randint(0,TOPIC_ALIAS_MAX)
    # pub_and_sub()
    

def on_message(mqttc, userdata, msg):
    print('received message: topic: %s payload: %s', msg.topic, msg.payload.decode())
    print("sending data to topic: %s", argsuments["pubTopic"])
    pub_and_sub()


mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(argsuments["endpoint"], 8883)


def hello():
    mqttc.loop_forever()

agent = Agent(name="alice")


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    # asyncio.run(hello())
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")
    hello()

if __name__ == "__main__":
    agent.run()
