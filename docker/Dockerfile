#FROM ubuntu:latest
#WORKDIR /app
# COPY ./requirements.txt /code/requirements.txt
# RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
#COPY ../ /app
#RUN ls
#RUN ["/bin/bash", "-c", "source venv/bin/activate"]
#RUN ["venv/bin/python", "-m", "server:app --host 0.0.0.0 --port 8081"]
#
#CMD . /app/venv/bin/activate && exec /app/venv/bin/python -m uvicorn server:app --reload --port 8081

# FROM python:3.9-slim-bullseye
# WORKDIR /app
# CMD . bin/sh -c "source /app/venv/bin/activate" && /app/venv/bin/python -m uvicorn server:app --reload --port 8081