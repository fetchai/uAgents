
# Fetch.ai - Megalo  📣
### Medical **Self Diagnosis** and **Doctors Search** Assistance System 


A Decentralised Agent based Medical Assistance System built on top of the [fetch.ai](https://fetch.ai/)  [`uagents`](https://pypi.org/project/uagents/) library








 




## 🤖 Megalo Agents Overview
### `Checkup Agent - Using API Medic`    
Entry point of the System where user checks up providing set of symptoms. 
Makes use of [APIMedic](https://apimedic.com/) to get issues
and specialisations associated with symptoms input


### `Clinics Agent - Using Bing Maps API`    
Get list of clinics, hospitals and Medical Institutions related to the symptoms and locally around the user's choice


### `Report Agent - Subtask`    
Prompt and Generate the Institutions and their locations, addresses, contacts for reaching out


### `Store Agent - MongoDB`    
Store resulting Institutions and records for logging, and later use






## 🔗 References


`Fetch ai docs`: Using Agents, AgentVerse and DeltaV

`uagents library`: Python package for autonomous Agents that works with the ai-engine on the AgentVerse

`DeltaV`: Interface between all agents on the AgentVerse

`APImedic`: External API for checking health issues and related given the symptoms and additional info.







## 🛠️  Setting Up

### `Get APIMedic Token`    
- Visit the [APIMedic Site](https://apimedic.com/apikeys)
- Register for [API key here](https://apimedic.com/apikeys)
- Add in the token section of `Checkup` Agent


### `Register for Bing`    
- Visit the [Bing Maps API Site](https://www.microsoft.com/en-us/maps/bing-maps/choose-your-bing-maps-api)
- After that, Register for [API key here](https://www.bingmapsportal.com/Application)
- Add in the token section of `Clinic` Agent


