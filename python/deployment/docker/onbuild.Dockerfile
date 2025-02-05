FROM python:3.12-slim-bookworm

WORKDIR /agent

ONBUILD COPY requirements.txt .
ONBUILD RUN pip3 install -r requirements.txt

ONBUILD COPY . /agent

ENTRYPOINT [ "python3", "/agent/agent.py" ]
CMD []
