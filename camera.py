import base64
import io
import time
from threading import Thread

import cv2
import numpy as np
import requests
from PIL import Image as Pil
from vidgear.gears import WriteGear


class ThreadedCameraStream(object):
    def __init__(self, src=''):
        self.frame = None
        self.video = None
        self.src = src
        self.update_var = 0
        self.frame_grabbed = False
        self.error = False
        self.stopped = False
        self.capture = None

        self.query_param_symbol = '&' if self.src.__contains__('?') else '?'
        self.is_image_stream = self.decide_image_stream()
        self.rtsp_url = 'rtsp://localhost:8554/' + \
                        str(base64.urlsafe_b64encode(self.src.encode("utf-8")), "utf-8").replace("=", "")[0:40]

        output_params = {"-f": "rtsp", "-rtsp_transport": "tcp"}

        if not self.error:
            try:
                if self.is_image_stream:
                    self.capture = cv2.VideoCapture(self.src)
                    grabbed, self.frame = self.capture.read()
                    if self.frame is None:
                        self.error = True
                    else:
                        self.writer = WriteGear(output_filename=self.rtsp_url, logging=True, **output_params)
                else:
                    self.writer = WriteGear(output_filename=self.rtsp_url, logging=True, **output_params)
            except Exception as e:
                print('Error while processing page (' + self.src + '): ' + e.__str__())
                self.error = True

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
                query_param = 'xyz=' + str(self.update_var)
                new_image_url = self.src + self.query_param_symbol + query_param
                self.update_var += 1
                response = requests.get(new_image_url)
                img_bytes = io.BytesIO(response.content)
                img = Pil.open(img_bytes)
                self.frame = np.asarray(img)
            time.sleep(self.FPS)

    def show_and_write_frame(self):
        try:
            if self.frame is not None:
                # cv2.imshow('frame', self.frame)
                self.writer.write(self.frame)
                cv2.waitKey(self.FPS_MS)
        except Exception:
            pass

    def decide_image_stream(self):
        if self.src.__contains__('.mjpg') or self.src.__contains__('stream'):
            return True
        if self.src.__contains__('jpg') or self.src.__contains__('jpeg') or self.src.__contains__('COUNTER'):
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
        if self.src.__contains__('GetData.cgi?CH='):
            self.error = True
            return True
        return True

    def run(self):
        while not self.error and not self.stopped:
            try:
                self.show_and_write_frame()
            except (AttributeError, KeyboardInterrupt):
                pass

        if self.capture is not None:
            self.capture.release()
        # safely close video stream
        if not self.error:
            self.writer.close()
        # safely close writer

    def stop(self):
        self.stopped = True


if __name__ == '__main__':
    # url = input('Enter URL with a camera image stream: ')
    # threaded_camera = ThreadedCameraStream('http://50.248.1.46:8000/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://73.226.128.200/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://174.141.213.150:9000/snap.jpg?JpegSize=M&JpegCam=1&r=COUNTER')
    # threaded_camera = ThreadedCameraStream('http://188.26.117.165/cgi-bin/faststream.jpg?stream=half&fps=3&rand=COUNTER')
    # threaded_camera = ThreadedCameraStream('https://lookcam.com/wagrowiec-panorama-of-town/')
    # threaded_camera = ThreadedCameraStream('http://70.190.171.110:82/GetData.cgi?CH=1')
    threaded_camera = ThreadedCameraStream('http://72.49.230.145:8080/?action=stream')
    # threaded_camera = ThreadedCameraStream('http://162.191.138.108:81/cgi-bin/camera?resolution=640&quality=1&Language=0&COUNTER')
    # threaded_camera = ThreadedCameraStream('http://24.245.57.160/nph-jpeg.cgi?0')
    # threaded_camera = ThreadedCameraStream('http://199.104.253.4/mjpg/video.mjpg')
    threaded_camera.run()
