from threading import Thread
from typing import List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from camera import ThreadedCameraStream

import scraper

app = FastAPI()


def delegate(*args):
    t = Thread(target=args[0].run())
    t.start()
    t.join()


class Data(BaseModel):
    video_page_url: str
    rtsp_url: str


@app.post("/scrape", status_code=200)
async def scrape(request: List[str]) -> Dict[str, List[Data]]:
    scraped_videos = {}
    results = scraper.find_videos_in_url_list(request)
    for scrap_url in results:
        scraped_videos[scrap_url] = []
        scrap, links_dict = results[scrap_url]
        video_urls = []
        for page_url in links_dict:
            page_links = links_dict[page_url]
            if len(page_links) == 0:
                continue
            for video_url in page_links:
                video_urls.append(video_url)
            scrap.init_cameras(video_urls)
            for camera in scrap.cameras:
                t = Thread(target=delegate, args=[camera])
                t.start()
                scraped_videos[scrap.src].append(
                    Data(
                        video_page_url=page_url,
                        rtsp_url=camera.rtsp_url,
                    )
                )
    return scraped_videos


@app.post("/stream", status_code=200)
async def scrape(request: List[str]) -> List[Data]:
    scraped_videos = []
    # todo and adjust the rest of the code
    return scraped_videos
