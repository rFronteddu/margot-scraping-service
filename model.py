from pydantic.main import BaseModel
from camera import ThreadedCameraStream


class Data(BaseModel):
    scraped_page_url: str
    video_page_url: str
    rtsp_url: str
    latitude: float = .0
    longitude: float = .0


class GeolocationModel:
    def __init__(self):
        self.country: str = ''
        self.city: str = ''
        self.place: str = ''
        self.latitude: float = .0
        self.longitude: float = .0


class CameraHolder:
    def __init__(self, camera: ThreadedCameraStream or None, lifespan: int, data: Data):
        self.camera = camera
        self.lifespan = lifespan
        self.data = data
