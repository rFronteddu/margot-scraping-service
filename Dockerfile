FROM python:3.9-slim-bullseye
ENV PYTHONUNBUFFERED 1
RUN mkdir "app"
COPY ./ /app
WORKDIR /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update
RUN apt-get install -y ffmpeg libsm6 libxext6