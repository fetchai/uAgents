PREFIX = """
You have control over several things in the room and based on user input you can control the lights, the air conditioning and the windows.

Appliances that can be controlled:
- "lights" : Lights can be turned on or off.
- "ac" : can be turned on or off and the temperature can be set.
- "window" : can be opened or closed and curtains can be put or removed.

Based on the user input, you need to decide which appliances to control and what action to take. 
"""

INSTRUCTIONS = """
- If user input makes you feel that room is empty, then you can turn off the lights, air conditioning and close the windows.
- To decide on "lights", think how it will affect the user comfort and the energy consumption.
- If turning on of a particular appliance is discomforting as per the user input, then you can choose to not turn it on.
- If you feel that a particular appliance is helpful for user as per the user input, then you can choose to turn it on.

USER INPUT:
{user_input}
"""

SUFFIX = """
RETURN_INSTRUCTIONS:
- Return a dictionary of sub-tasks with appliance name as key and the action to be taken as value. 
- Do not return anything else. Nothing else should be returned in the result. Only the dictionary within curly braces.
- Double check that there are no parsing errors.

"""

# ______________________________________________________________________________________________________________________________________________


FUNCTION_PARAMETER_PROMPT = """
You are supposed to extract the values of function parameters from user input and return them in a dictionary. 
These extracted parameters will be used to make a fuction call later....

Below are the parameters and their data-type that the function takes:
{function_parameters}

I also provide you with the description of these parameters to help you reason out right values for these parameters.
{parameter_description}

USER INPUT:
{user_input}


RETURN INSTRUCTIONS:
- Return a dictionary of function parameters with parameter name as key and the value as value.
- Do not return anything else.
- Ensure that the result is in correct format, otherwise there will be parsing errors.
"""
