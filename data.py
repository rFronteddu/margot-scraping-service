from pydantic.main import BaseModel
from camera import ThreadedCameraStream


class Data(BaseModel):
    scraped_page_url: str
    video_page_url: str
    rtsp_url: str
    country: str = ''
    city: str = ''
    place: str = ''
    latitude: float = .0
    longitude: float = .0


class CameraHolder:
    def __init__(self, camera: ThreadedCameraStream, lifespan: int, data: Data):
        self.camera = camera
        self.lifespan = lifespan
        self.data = data
