# USGS Earthquake Details Agent
If provided an earthquake ID, this agent will query the USGS API for the corresponding earthquake's details, formatting fields to provide users the details in a readble manner.

## Overview

The United States Geological Survey (USGS) assigns individual earthquakes IDs to uniquely identify between events. This being said, each earthquake, correspondingly, has unique details (ex. magnitude, latitude and longitude).
<br><br>
This DeltaV compatible agent takes a USGS-assigned earthquake id as an input and will return a formatted list of details pertaining to the earthquake.

## Prerequisites

To use this integration you'll need:
- Access to the Agentverse
- Access to DeltaV

## Steps to Use the Integration
To use this integ

## Steps to run this Agent
Want to run this agent yourself through the Agentverse? Follow these steps:

### 1. Create this Agent in the **Agentverse**

1. Login to [Agentverse](https://agentverse.ai) and create a `New Agent`.
2. Select `Blank Agent` and assign a name to your agent (ex.
USGS Earthquake Details Agent)
3. Copy the content from `get_usgs_eq_details.py` into `agent.py`.
5. Click on `Start` to start the agent; it's now running in the Agentverse!

### 2. Register the Agent as a Function

1. Once the agent is running, select `Deploy` and create a `New Function`.
2. Provide a function title, like:
```USGS Earthquake Details```
3. Provide a function description for the AI Engine. For example:
```
"This function will provide formatted details given a USGS earthquake ID."
```
4. This function will be a primary function. The fields `Protocol` and `Data Model`
 should automatically be filled out with `USGS Earthquake Protocol` and `USGS_ID` respectively.
5. Provide an extended description for the AI Engine. For example:
```
If a USGS (United States Geological Survey) earthquake ID is provided, this function will provide earthquake details in a formatted manner to the user. This is MUST be a string and not a URL or webpage address.
```

### 3. Access the Service/Agent on DeltaV

1. Login to [DeltaV](https://deltav.agentverse.ai/home). Assuming you have enough currency, you can query your newly created Agent and function.
2. Find a USGS-assigned earthquake ID online. An example could be `ci38457511`, which is the earthquake ID for the popular Ridgequest Earthquake Sequence's main event.
3. Type in a query related to getting earthquake data. For example:
```
Could you provide me the earthquake details for earthquake id ci38457511?
```
4. Using `Advanced Options`, choose `My Functions`. Then, start the conversation to get earthquake details.
