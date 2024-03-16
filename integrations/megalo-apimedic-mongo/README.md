
# Fetch.ai - Megalo  📣
### Medical **Self Diagnosis** and **Doctors Search** Assistance System 


A Decentralised Agent based Medical Assistance System built on top of the [fetch.ai](https://fetch.ai/)  [`uagents`](https://pypi.org/project/uagents/) library



## 🤖 Megalo Agents Overview

### `Checkup Agent - Using API Medic`    
Entry point of the System where user checks up providing set of symptoms. 
Makes use of [APIMedic](https://apimedic.com/) to get issues
and specialisations associated with symptoms input <br />
[Additional Guide to this Agent](https://github.com/ShubhamTiwary914/uAgents/blob/main/integrations/megalo-apimedic-mongo/src/agents/checkup/README.md)


### `Clinics Agent - Using Bing Maps API`    
Get list of clinics, hospitals and Medical Institutions related to the symptoms and locally around the user's choice <br />
[Additional Guide to this Agent](https://github.com/ShubhamTiwary914/uAgents/blob/main/integrations/megalo-apimedic-mongo/src/agents/store/README.md)


### `Report Agent - Subtask`    
Prompt and Generate the Institutions and their locations, addresses, contacts for reaching out


### `Store Agent - MongoDB`    
Store resulting Institutions and records for logging, and later use <br />
[Additional Guide to this Agent](https://github.com/ShubhamTiwary914/uAgents/blob/main/integrations/megalo-apimedic-mongo/src/agents/store/README.md)






## 🔗 References


`Fetch ai docs`: Using Agents, AgentVerse and DeltaV

`uagents library`: Python package for autonomous Agents that works with the ai-engine on the AgentVerse

`DeltaV`: Interface between all agents on the AgentVerse

`APImedic`: External API for checking health issues and related given the symptoms and additional info.

`Bing Maps API`: Open Source Maps API for GeoEncode-Decode and Location based queries

`MongoDB (pymongo)`: Archives Logs of institutions found near users with symptoms matched





## 🛠️  Setting Up

### `Get APIMedic Token`    
- Visit the [APIMedic Site](https://apimedic.com/apikeys)
- Register for [API key here](https://apimedic.com/apikeys)
- Add in the token section of `Checkup` Agent


### `Register for Bing`    
- Visit the [Bing Maps API Site](https://www.microsoft.com/en-us/maps/bing-maps/choose-your-bing-maps-api)
- After that, Register for [API key here](https://www.bingmapsportal.com/Application)
- Add in the token section of `Clinic` Agent




## Setting up Agents 
### Setting up on Agentverse
![image](https://github.com/ShubhamTiwary914/uAgents/assets/67773966/271ea199-752a-4372-9f5c-f8d59466e975)

- Go to [Agentverse -> agents](https://agentverse.ai/agents) and start the individual agents
- These active agents are listen on the Agentverse via the Alamanac Contract


### Setting up a Service
![image](https://github.com/ShubhamTiwary914/uAgents/assets/67773966/7f70d3c2-984d-4928-b96a-eb4552c97e83)

- Then create services for the created Agents


### Run Service on DeltaV

![image](https://github.com/ShubhamTiwary914/uAgents/assets/67773966/ba4a99f2-79b5-4b3c-baf3-755d6608cfc2)

- Finally, Interact with the Service on DeltaV




