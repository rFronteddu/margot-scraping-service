from pydantic.main import BaseModel


class Data(BaseModel):
    video_page_url: str
    rtsp_url: str
