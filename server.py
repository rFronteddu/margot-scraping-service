import threading
import time
from collections import namedtuple
from threading import Thread
from typing import List, Dict, Tuple

import requests
from fastapi import FastAPI

from camera import ThreadedCameraStream
from data import Data

import scraper

app = FastAPI()

active_cameras: Dict[str, Tuple[ThreadedCameraStream, int]] = {}
cameras_to_remove = []


def get_extended_lifespan() -> int:
    return int(time.time().__add__(60 * 5))


def remove_expired_cameras():
    active_paths = get_active_streams_paths()
    for url in active_cameras.keys():
        camera, validity = active_cameras[url]
        for path in active_paths:
            if url.__contains__(path):
                new_time = get_extended_lifespan()
                active_cameras[url] = camera, new_time
                print('increased lifetime of ' + url + ' to ' + str(new_time))
        print(str(validity) + ' --- ' + str(int(time.time())) + '= ' + str(validity < int(time.time())))
        if validity < int(time.time()):
            cameras_to_remove.append(url)
            camera.stop()
    for url in cameras_to_remove:
        active_cameras.pop(url)


def get_active_streams_paths() -> List[str]:
    response = requests.get("http://localhost:9997/v1/paths/list")
    stream_paths = []
    if response.status_code == 200:
        json_response = response.json()
        items = json_response['items']
        for path in items.keys():
            if len(items[path]['readers']) > 0:
                stream_paths.append(path)
    return stream_paths


def purge_inactive_camera_delegate():
    ticker = threading.Event()
    while not ticker.wait(60):
        remove_expired_cameras()


def camera_start_delegate(*args):
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
            t = Thread(target=camera_start_delegate, args=[camera])
            t.start()
            active_cameras[camera.rtsp_url] = camera, get_extended_lifespan()
        scraped_videos[scrap_url] = scrap.found_data
    return scraped_videos


@app.post("/stream", status_code=200)
async def stream(request: List[str]) -> List[Data]:
    return_data: List[Data] = []
    for url in request:
        scrap = scraper.Scraper(url, True)
        data, camera = scrap.init_camera()
        t = Thread(target=camera_start_delegate, args=[camera])
        t.start()
        active_cameras[camera.rtsp_url] = camera, get_extended_lifespan()
        return_data.append(data)
    return return_data


thread = Thread(target=purge_inactive_camera_delegate)
thread.start()
