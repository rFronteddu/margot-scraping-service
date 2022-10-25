from selenium.webdriver.common.by import By
from scraper import Scraper
import time
from vidgear.gears import StreamGear, CamGear
import cv2


def a():
    # open any valid video stream(from web-camera attached at index `0`)
    stream = CamGear(source='http://199.104.253.4/mjpg/video.mjpg').start()

    # enable livestreaming and retrieve framerate from CamGear Stream and
    # pass it as `-input_framerate` parameter for controlled framerate
    stream_params = {"-input_framerate": 1, "-livestream": True}
    print(stream.framerate)

    # describe a suitable manifest-file location/name
    streamer = StreamGear(output="hls_out.m3u8", format="hls", **stream_params)

    # loop over
    while True:

        # read frames from stream
        frame = stream.read()

        # check for frame if Nonetype
        if frame is None:
            break

        # {do something with the frame here}

        # send frame to streamer
        streamer.stream(frame)

        # Show output window
        cv2.imshow("Output Frame", frame)

        # check for 'q' key if pressed
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    # close output window
    cv2.destroyAllWindows()

    # safely close video stream
    stream.stop()

    # safely close streamer
    streamer.terminate()


# src = 'https://lookcam.com/wagrowiec-panorama-of-town/'
# scrap = Scraper(src)
# browser = scrap.init_browser()
#
# browser.get(src)
# a = browser.page_source
# scrap.remove_site_cookies_popup()
# res = browser.find_elements(By.XPATH, "//*[contains(.,'52.8067972')]")
# for r in res:
#    print(r.text)


if __name__ == '__main__':
    a()
