# FROM aler9/rtsp-simple-server AS rtsp
# FROM alpine:3.12
# RUN apk add --no-cache ffmpeg
# COPY --from=rtsp /rtsp-simple-server /
# COPY --from=rtsp /rtsp-simple-server.yml /
# ENTRYPOINT [ "/rtsp-simple-server" ]
# Using the Ubuntu image (our OS)
FROM ubuntu:latest
# Update package manager (apt-get)
# and install (with the yes flag `-y`)
# Python and Pip
RUN apt-get update && apt-get install -y python3.9 python3-pip
RUN rm /bin/sh && ln -s /bin/bash /bin/sh
WORKDIR /api/
RUN python3 -m pip install fastapi
RUN python3 -m pip install uvicorn
RUN python3 -m pip install -U vidgear[core]
RUN python3 -m pip install Pillow
RUN python3 -m pip install selenium
RUN python3 -m pip install webdriver-manager