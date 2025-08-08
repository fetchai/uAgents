# uAgent Deployment Example

We provide here an example of Dockerfile and Helm deployment charts for a simple uAgent.

## Prerequisites

- Install docker: https://docs.docker.com/get-docker/
- Sign up for a Dockerhub account: https://hub.docker.com/
- Install kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl/
- Install helm: https://helm.sh/docs/intro/install/

## Docker

### Building the Docker Image

1. Navigate to the directory containing the Dockerfile:

```bash
cd hello-agent
```

2. Build the Dockerfile

```bash
docker build --tag my-dockerhub-id/hello-agent:0.1 .
```

3. Sign in to Dockerhub

```bash
docker login
```

4. Push the Docker image to Dockerhub

```bash
docker push my-dockerhub-id/hello-agent:0.1
```

## Helm

### Configuring the Helm Chart

1. Edit the `values.yaml` file in the `helm/uagent` directory to include the Dockerhub image you pushed in the previous step.

```yaml
image:
  repository: "fetchai/hello-agent"
  pullPolicy: IfNotPresent
  tag: "0.1"
```

2. Configure the agent details:

```yaml
agent:
  name: <agent's public name>
  seed: <unique seed phrase>
  type: "custom" # mailbox, proxy, custom (default)
  network: "testnet" # testnet, mainnet
  portName: http
  port: 8000
```

### Deploying the Agent

1. Install the helm release:

```bash
helm install hello-agent .
```

2. Check your agents are running:

```bash
kubectl get pods
```

3. Check the logs of the agent:

```bash
kubectl logs hello-agent-<pod-id>
```
