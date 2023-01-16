
NOTE: INCOMPLETE
# Remote agents

uAgents can also interact remotely from different terminals. All you would need to now is the recipient agent address.
You can print you uAgent address at any time by running `my_agent.address`

## Registration

- Each uAgent needs to register in a smart contract almanac in order to be found by other uAgents.
- To register, an uAgent provides its address along with metadata about the service endpoints that it provides.
- They have to pay a small fee for this registration.
- In order to keep the registration information up to date, the agent will need to continually re-register their information.
- Each individual uAgent can query the current active registrations for information to communicate with other agents.
- uAgents can communicate by retrieving an HTTP endpoint from the recipient uAgent.
