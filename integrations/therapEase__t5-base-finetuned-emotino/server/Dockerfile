FROM python:3.9-slim-buster
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
ENV FLASK_APP=my_flask.py
CMD ["python", "run.py"]