import threading
import time
import scraper
import requests

from threading import Thread
from typing import List, Dict
from fastapi import FastAPI
from model import Data, CameraHolder
from datetime import datetime

app = FastAPI()

active_cameras: Dict[str, CameraHolder] = {}


def get_extended_lifespan() -> int:
    return int(time.time().__add__(60 * 5))


def remove_expired_cameras():
    cameras_to_remove = []
    active_paths = get_active_streams_paths()
    for url in active_cameras.keys():
        camera_holder = active_cameras[url]
        for path in active_paths:
            if url.__contains__(path):
                new_time = get_extended_lifespan()
                camera_holder.lifespan = new_time
                print('Increased lifespan of ' + camera_holder.data.rtsp_url)
        if camera_holder.lifespan < int(time.time()):
            cameras_to_remove.append(url)
            if camera_holder.camera is not None:
                camera_holder.camera.stop()
            print('stopped camera ' + url)
    for url in cameras_to_remove:
        del active_cameras[url]
    cameras_to_remove.clear()


def get_active_streams_paths() -> List[str]:
    response = requests.get("http://rtsp-server:9997/v1/paths/list")
    stream_paths = []
    if response.status_code == 200:
        json_response = response.json()
        items = json_response['items']
        for path in items.keys():
            if len(items[path]['readers']) > 0:
                stream_paths.append(path)
    return stream_paths


def scrape_url_list(request: List[str]):
    results = scraper.find_videos_in_url_list(request)
    for scrap_url in results:
        scrap = results[scrap_url]
        cameras = scrap.init_cameras(active_cameras.values())
        for data in scrap.found_data:
            camera = next((x for x in cameras if x.rtsp_url == data.rtsp_url), None)
            if camera is not None:
                t = Thread(target=camera_start_delegate, args=[camera])
                t.start()
            active_cameras[data.rtsp_url] = \
                CameraHolder(
                    camera,
                    get_extended_lifespan(),
                    data
                )


def purge_inactive_camera_delegate():
    ticker = threading.Event()
    while not ticker.wait(60):
        remove_expired_cameras()


def camera_start_delegate(*args):
    t = Thread(target=args[0].run())
    t.start()
    t.join()


def scrape_start_delegate(*args):
    t = Thread(target=args[0](args[1]))
    t.start()
    t.join()


@app.post("/scrape", status_code=200)
async def scrape(request: List[str]):
    t = Thread(target=scrape_start_delegate, args=[scrape_url_list, request])
    t.start()
    return datetime.now()


@app.get("/videos", status_code=200)
async def videos() -> List[Data]:
    scraped_videos = []
    for path in active_cameras:
        scraped_videos.append(active_cameras[path].data)
    return scraped_videos


thread = Thread(target=purge_inactive_camera_delegate)
thread.start()
