from pydantic.main import BaseModel


class Data(BaseModel):
    scraped_page_url: str
    video_page_url: str
    rtsp_url: str
    country: str = ''
    city: str = ''
    place: str = ''
    latitude: float = .0
    longitude: float = .0

