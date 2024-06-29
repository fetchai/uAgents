# Use Python 3.9 to install poetry and export requirements, since poetry itself is compatible with this version.
FROM python:3.9 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
# Copy pyproject.toml and poetry.lock (if exists) into the temporary image
COPY ./pyproject.toml ./poetry.lock* /tmp/
# Export the project dependencies to a requirements.txt file
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Now, switch to the Python 3.11 image for the final stage, as specified in your pyproject.toml
FROM python:3.11
WORKDIR /code
# Copy the requirements.txt from the previous stage
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
# Install dependencies from the requirements.txt file without caching to keep the image small
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
# Copy your application code into the image
COPY ./src/agents/utils /code/

# Specify the command to run your FastAPI application using Uvicorn
# Given the project structure, adjust the Uvicorn command to reflect the correct path to main.py
CMD ["uvicorn", "ncert:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8080", "--reload"]
