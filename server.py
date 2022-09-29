from threading import Thread
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

import camera

app = FastAPI()


def delegate(*args):
    t = Thread(target=args[0].run())
    t.start()
    t.join()


class Data(BaseModel):
    base_url: str
    rtsp_url: str


@app.post("/scrape", status_code=200)
async def scrape(request: List[str]) -> List[Data]:
    scraped_videos = []
    for url in request:
        threaded_camera = camera.ThreadedCameraStream(url)
        t = Thread(target=delegate, args=[threaded_camera])
        t.start()
        scraped_videos.append(
            Data(
                base_url=url,
                rtsp_url=threaded_camera.rtsp_url,
            )
        )
    return scraped_videos
