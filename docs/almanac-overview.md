# Almanac Contract

Agents of the system will be [registered](almanac-registration.md) in the almanac contract. Users can query a particular agent's information directly from the contract to communicate.

A central part of the system is that registrations are strictly time (in blocks) limited.
This primarily helps with the liveness problem when dealing with a large ecosystem of agents.
In order to keep the registration information up to date, the agent will need to continually re-register
their information with the index.

When an agent’s information times out, queries for that agent will no longer return the registered information. 
This is handled by the query logic since technically, the previous service information is still stored on the blockchain.

With each registration, the agent will need to prove ownership of 
the [agent address](addresses.md) by signing a sequence number with their uAgent private key and submitting the 
signature for verification on the contract. This sequence number should increment with each successful registration and should also be queryable. This will be performed automatically.