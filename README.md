# Web scraping service
This service exposes an API for scraping videos contained in a passed list of URLs. Its main goal is form the response containing relevant information about found videos (such as Geolocation) from scraped information. The application utilizes libraries such as [VidGear](https://abhitronix.github.io/vidgear) which is a library based on OpenCV, and [FastAPI](https://fastapi.tiangolo.com) for API hosting.

All found videos are streamed via RTSP protocol, which can be opened for instance in VLC player. Streams are valid for 5 minutes. Watching any of the streams will increase its lifespan, so when user quits watching the stream it will still be active for another five minutes.

## How to run it
This project is meant to run in Docker. It consists of three separate parts that communicate with each other. 
- [RtspSimpleServer](https://github.com/aler9/rtsp-simple-server) for providing endpoint to which the video content should be streamed
- [SeleniumStandaloneChromium](https://registry.hub.docker.com/r/seleniarm/standalone-chromium) network accessible version of an internet browser that does the actual scraping (this part was necessary since selenium itself does not work natively on each and every platform, including some operating systems or cpu architectures - in this case it might be necessary to adjust image that suites the target machine - more info on the official page of [Docker-Selenium](https://github.com/SeleniumHQ/docker-selenium))
- The actual Python application that contains all application logic, such as hosting an API, scraping logic or streaming videos to RtspServer
   
There is a *docker-compose.yml* file for running the project very easily by calling a command bellow from a terminal.  
   
`docker-compose up`  

## API endpoints
The endpoints are accessible by default on the 8081 port (could be adjusted in docker-compose file).   
   
Currently, there are three endpoints available: 
* This endpoint accepts a parameter - a list of string that should represent URL addresses from which the video streams should be extracted. By calling this endpoint, a confirmation about start of scraping is returned as a response, the found data will be available on the */videos* endpoint.
    > POST: /scrape
* As mentioned above, the next endpoint returns all currently streamed videos with all collected information.
    > GET: /videos
* The last endpoint accepts a direct video link that should be streamed from the server. When the stream is ready, its rtsp link will be returned.
    > POST: /stream

**NOTE: Not all videos can be processed by this application. There are a few formats that OpenCV cannot work with and thus, an error message will be returned.**

   

