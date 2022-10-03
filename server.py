from threading import Thread
from typing import List, Dict

from fastapi import FastAPI
from data import Data

import scraper

app = FastAPI()


def delegate(*args):
    t = Thread(target=args[0].run())
    t.start()
    t.join()


@app.post("/scrape", status_code=200)
async def scrape(request: List[str]) -> Dict[str, List[Data]]:
    scraped_videos = {}
    results = scraper.find_videos_in_url_list(request)
    for scrap_url in results:
        scrap = results[scrap_url]
        for camera in scrap.init_cameras():
            t = Thread(target=delegate, args=[camera])
            t.start()
        scraped_videos[scrap_url] = scrap.found_data
    return scraped_videos


@app.post("/stream", status_code=200)
async def scrape(request: List[str]) -> List[Data]:
    scraped_videos = []
    # todo and adjust the rest of the code
    return scraped_videos
