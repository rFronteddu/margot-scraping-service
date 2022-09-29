import base64
import io
import time
from threading import Thread

import PIL.Image as pil
import cv2
import numpy as np
import requests
from vidgear.gears import WriteGear
import scraper


class ThreadedCameraStream(object):
    def __init__(self, src=''):
        self.frame = None
        self.video = None
        self.src = src
        self.update_var = 0

        self.query_param_symbol = '?' if self.src.__contains__('?') else '&'
        self.is_image_stream = self.decide_image_stream()
        self.rtsp_url = 'rtsp://localhost:8554/' + base64.b64encode(bytes(self.src, 'utf-8')).decode('utf-8')

        try:
            if self.is_image_stream:
                self.capture = cv2.VideoCapture(self.src)
        except cv2.error as e:
            print('Error while processing page ('+self.src+') ' + e)
            self.rtsp_url = ''

        output_params = {"-f": "rtsp", "-rtsp_transport": "tcp"}
        self.writer = WriteGear(output_filename=self.rtsp_url, compression_mode=True, logging=True,
                                **output_params)

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
                if self.capture.isOpened() and self.rtsp_url != '':
                    (self.status, self.frame) = self.capture.read()
            else:
                query_param = 'a=' + str(self.update_var)
                new_image_url = self.src + self.query_param_symbol + query_param
                print(new_image_url)
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
        if self.src.__contains__('mjpg'):
            return True
        if self.src.__contains__('stream'):
            return True
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
        found_url = scraper.Scraper(self.src).get_blob_video_url()
        if found_url is not None:
            self.src = found_url
        return True

    def run(self):
        while True:
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
        self.writer.close()
        # safely close writer


if __name__ == '__main__':
    # url = input('Enter URL with a camera image stream: ')
    # threaded_camera = ThreadedCameraStream('http://50.248.1.46:8000/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://73.226.128.200/mjpg/video.mjpg')
    # threaded_camera = ThreadedCameraStream('http://188.210.92.19/oneshotimage1?1663785150')
    # threaded_camera = ThreadedCameraStream('http://188.26.117.165/cgi-bin/faststream.jpg?stream=half&fps=3&rand=COUNTER')
    threaded_camera = ThreadedCameraStream('https://lookcam.com/wagrowiec-panorama-of-town/')
    threaded_camera.run()



