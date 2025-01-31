FROM python:3.12-slim-bookworm

WORKDIR /agent

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /agent

ENTRYPOINT [ "python3", "/agent/agent.py" ]
CMD []
