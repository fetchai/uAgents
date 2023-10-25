<a id="src.uagents.mailbox"></a>

# src.uagents.mailbox

<a id="src.uagents.mailbox.MailboxClient"></a>

## MailboxClient Objects

```python
class MailboxClient()
```

Client for interacting with the Agentverse mailbox server.

<a id="src.uagents.mailbox.MailboxClient.base_url"></a>

#### base`_`url

```python
@property
def base_url()
```

Property to access the base url of the mailbox server.

Returns: The base url of the mailbox server.

<a id="src.uagents.mailbox.MailboxClient.api_key"></a>

#### api`_`key

```python
@property
def api_key()
```

Property to access the api key of the mailbox server.

Returns: The api key of the mailbox server.

<a id="src.uagents.mailbox.MailboxClient.protocol"></a>

#### protocol

```python
@property
def protocol()
```

Property to access the protocol of the mailbox server.

Returns: The protocol of the mailbox server {http, https}.

<a id="src.uagents.mailbox.MailboxClient.http_prefix"></a>

#### http`_`prefix

```python
@property
def http_prefix()
```

Property to access the http prefix of the mailbox server.

Returns: The http prefix of the mailbox server {http, https}.

<a id="src.uagents.mailbox.MailboxClient.run"></a>

#### run

```python
async def run()
```

Runs the mailbox client. Acquires an access token if needed and then starts a polling loop.

<a id="src.uagents.mailbox.MailboxClient.process_deletion_queue"></a>

#### process`_`deletion`_`queue

```python
async def process_deletion_queue()
```

Processes the deletion queue. Deletes envelopes from the mailbox server.

