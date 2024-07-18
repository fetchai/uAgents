## Expectation:


Questions and [Expectations]
1. How many agents do I have? [postgres]
2. How many mailbox do I have? [mailbox]
3. How many users don't have a name? [postgres]


### Test Database Set #1
```
[
    {
        "host": "postgresql://postgres:myverystrongpasswordnoonecanguess@localhost:5499/postgres",
        "name": "postgres",
        "description": "The name of this database is postgres in lowercase. postgres is the default database whenever you are unsure return this database name. Whenever someone is looking for agents their name, description or details also choose this database.",
    },
    {
        "host": "postgresql://postgres:myverystrongpasswordnoonecanguess@localhost:5499/postgres",
        "name": "mailbox",
        "description": "The name of this database is mailbox in lowercase. mailbox is the the database name you return whenever someone is looking for access to local agents, they can also have a name and an address. ",
    },
]
```

1. `mailbox` [WRONG]
2. `mailbox` [RIGHT]
3. `postgres` [RIGHT]



### Test Database Set #2

```
[
    {
        "host": "postgresql://postgres:myverystrongpasswordnoonecanguess@localhost:5499/postgres",
        "name": "postgres",
        "description": "This database is called postgres in lowercase. postgres is the default database whenever you are unsure return this database name. Whenever someone is looking for agents or their name, description and details choose this database. Important: Don't use this if someone is looking for mailboxes.",
    },
    {
        "host": "postgresql://postgres:myverystrongpasswordnoonecanguess@localhost:5499/postgres",
        "name": "mailbox",
        "description": "This database is called mailbox in lowercase. mailbox is the the database you return whenever someone is looking for access to local agents called mailboxes. Important: Don't use this if someone is looking for agents or you are unsure.",
    },
]
```

1. `mailbox` [RIGHT]
2. `mailbox` [RIGHT]
3. `postgres` [RIGHT]