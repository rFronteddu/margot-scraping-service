import io
import time
import uuid
from threading import Thread

from PIL import Image as pil
import cv2
import numpy as np
import requests
from vidgear.gears import WriteGear, CamGear
from urllib import request


class ThreadedCameraStream(object):
    def __init__(self, src=''):
        self.frame = None
        self.video = None
        self.src = src
        self.update_var = 0
        self.frame_grabbed = False
        self.error = False

        self.query_param_symbol = '&' if self.src.__contains__('?') else '?'
        self.is_image_stream = self.decide_image_stream()
        self.rtsp_url = 'rtsp://localhost:8554/' + str(uuid.uuid4()).replace('-', '')

        output_params = {"-f": "rtsp", "-rtsp_transport": "tcp"}

        try:
            if self.is_image_stream:
                # self.capture = CamGear(source=self.src, logging=False).start()
                try:
                    self.capture = cv2.VideoCapture(self.src)
                    grabbed, self.frame = self.capture.read()
                    if self.frame is None:
                        self.error = True
                    else:
                        self.writer = WriteGear(output_filename=self.rtsp_url, logging=True, **output_params)
                except Exception as e:
                    raise e
            else:
                self.writer = WriteGear(output_filename=self.rtsp_url, logging=True, **output_params)
        except Exception as e:
            print('Error while processing page (' + self.src + ') ' + e.__str__())
            raise e

        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1 / 30
        self.FPS_MS = int(self.FPS * 1000)

        # Start frame retrieval thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while True:
            if self.is_image_stream:
                if self.rtsp_url != '' and not self.error:
                    grabbed, self.frame = self.capture.read()
            else:
                query_param = 'a=' + str(self.update_var)
                new_image_url = self.src + self.query_param_symbol + query_param
                self.update_var += 1
                response = requests.get(new_image_url)
                img_bytes = io.BytesIO(response.content)
                img = pil.open(img_bytes)
                self.frame = np.asarray(img)
            time.sleep(self.FPS)

    def show_and_write_frame(self):
        if self.frame is not None:
            # cv2.imshow('frame', self.frame)
            self.writer.write(self.frame)
            cv2.waitKey(self.FPS_MS)

    def decide_image_stream(self):
        if self.src.__contains__('.mjpg') or self.src.__contains__('stream') or self.src.__contains__('GetData.cgi?CH='):
            return True
        if self.src.__contains__('jpg') or self.src.__contains__('jpeg'):
            return False
        if self.src.__contains__('?'):
            query_param = self.src.split('?').__getitem__(1)
            num = ''
            last_numeric = False
            for char in query_param:
                if last_numeric and num.__len__() >= 6:
                    return False
                if char.isnumeric():
                    num += char
                    last_numeric = True
                else:
                    num = ''
                    last_numeric = False
        if self.src.__contains__('COUNTER'):
            return False
        # found_url = scraper.Scraper(self.src).get_blob_video_url()
        # if found_url is not None:
        #     self.src = found_url
        return True

    def run(self):
        while not self.error:
            try:
                self.show_and_write_frame()
            except AttributeError:
                pass
            except KeyboardInterrupt:
                pass

            key = cv2.waitKey(1) & 0xFF
            # check for 'q' key-press
            if key == ord("q"):
                # if 'q' key-pressed break out
                break

        cv2.destroyAllWindows()
        # close output window

        self.capture.release()
        # safely close video stream
        if not self.error:
            self.writer.close()
        # safely close writer


if __name__ == '__main__':
    # url = input('Enter URL with a camera image stream: ')
    # threaded_camera = ThreadedCameraStream('http://50.248.1.46:8000/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://73.226.128.200/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://174.141.213.150:9000/snap.jpg?JpegSize=M&JpegCam=1&r=COUNTER')
    # threaded_camera = ThreadedCameraStream('http://188.26.117.165/cgi-bin/faststream.jpg?stream=half&fps=3&rand=COUNTER')
    # threaded_camera = ThreadedCameraStream('https://lookcam.com/wagrowiec-panorama-of-town/')
    # threaded_camera = ThreadedCameraStream('http://70.190.171.110:82/GetData.cgi?CH=1')
    # threaded_camera = ThreadedCameraStream('http://162.191.138.108:81/cgi-bin/camera?resolution=640&quality=1&Language=0&COUNTER')
    # threaded_camera = ThreadedCameraStream('http://24.245.57.160/nph-jpeg.cgi?0')
    threaded_camera = ThreadedCameraStream('http://199.104.253.4/mjpg/video.mjpg')
    threaded_camera.run()
