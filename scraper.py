import json
import time
from typing import List, Dict, Tuple

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from camera import ThreadedCameraStream
from data import Data

sleep_time = 0.5


class Scraper:
    def __init__(self, src: str, direct_video_link: bool = False):
        self.src = src
        self.cameras = []
        self.browser = None
        if not direct_video_link:
            self.init_browser()
            self.found_data: List[Data] = []

    def init_browser(self) -> WebDriver:
        chrome_options = Options()
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager(version='106.0.5249.21').install()),
                                        desired_capabilities=desired_capabilities,
                                        options=chrome_options)
        return self.browser

    def remove_site_cookies_popup(self):
        time.sleep(sleep_time)
        if len(self.browser.find_elements(By.CLASS_NAME, "css-47sehv")) > 0:
            element = WebDriverWait(self.browser, 2000).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "css-47sehv")))
            element.click()

    def get_blob_video_url(self, cookies_consent: bool = True) -> str:
        try:
            if self.browser is None:
                self.init_browser()
            self.browser.get(self.src)
            if not cookies_consent:
                self.remove_site_cookies_popup()
            class_players = self.browser.find_elements(By.CLASS_NAME, "player")
            if class_players.__len__() > 0:
                element = WebDriverWait(self.browser, 2000).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "player")))
                element.click()
            else:
                tag_players = self.browser.find_elements(By.TAG_NAME, "player")
                if tag_players.__len__() > 0:
                    element = WebDriverWait(self.browser, 2000).until(
                        EC.element_to_be_clickable((By.TAG_NAME, "player")))
                    element.click()
                else:
                    id_players = self.browser.find_elements(By.ID, "player")
                    if id_players.__len__() > 0:
                        element = WebDriverWait(self.browser, 2000).until(
                            EC.element_to_be_clickable((By.ID, "player")))
                        element.click()
            performance_log = self.browser.get_log('performance')
            network_extra_info = []
            for i in performance_log:
                response = json.loads(i.get('message'))
                if response.get('message').get('method') == 'Network.requestWillBeSentExtraInfo':
                    m = i.get('message')
                    upd = str(m).replace("false", "False").replace("true", "True")
                    network_extra_info.append(m)
                    message = eval(upd)
                    headers = message.get('message').get('params').get('headers')
                    path = headers.get(':path')
                    if path:
                        find_content = str(path).__contains__("hlsplaylist.html") or str(path).__contains__("m3u8")
                        if find_content:
                            authority = headers.get(':authority')
                            scheme = headers.get(':scheme')
                            return scheme + '://' + authority + path
        except Exception as e:
            print(e)
            pass
        except NoSuchElementException:
            pass

    def find_video_links_on_page(self) -> List[str]:
        videos_urls = []
        self.browser.get(self.src)
        self.remove_site_cookies_popup()
        a_links = self.browser.find_elements(By.TAG_NAME, 'a')
        for a_element in a_links:
            if a_element.find_element(By.XPATH, '..').tag_name.__eq__('div') and \
                    any(
                        child.tag_name == 'img' for child in a_element.find_elements(By.XPATH, './/*')
                    ) and a_element.size['width'] > 100 and a_element.size['height'] > 100:
                videos_urls.append(a_element.get_attribute('href'))
        return videos_urls

    def find_video_source_on_page(self, url_list: List[str]) -> List[Data]:
        videos_urls = []
        for url in url_list:
            self.browser.get(url)
            time.sleep(sleep_time)
            videos = self.browser.find_elements(By.TAG_NAME, 'video')
            for video in videos:
                try:
                    if video.size['width'] < 10 and video.size['height'] < 10:
                        continue
                    video_src = video.get_attribute('src')
                    if video_src is None or video_src == '':
                        video_children = video.find_elements(By.XPATH, './/*')
                        for child in video_children:
                            child_src = child.get_attribute('src')
                            if child_src is not None and child_src != '':
                                videos_urls.append(Data(
                                    video_page_url=url,
                                    rtsp_url=child_src,
                                ))
                    if video_src is not None and video_src != '':
                        pure_video_source = video_src \
                            if not video_src.__contains__('blob') \
                            else self.get_blob_video_url()
                        videos_urls.append(Data(
                            video_page_url=url,
                            rtsp_url=pure_video_source
                        ))
                except StaleElementReferenceException:
                    pass
        return videos_urls

    def init_camera(self, data: Data = None) -> Tuple[Data, ThreadedCameraStream]:
        rtsp_url = self.src if data is None else data.rtsp_url
        camera = ThreadedCameraStream(rtsp_url)
        if camera.error:
            try:
                pure_url = self.get_blob_video_url(False)
                if not pure_url.__eq__(self.src) and pure_url != '' and pure_url is not None:
                    rtsp_url = pure_url
                camera = ThreadedCameraStream(rtsp_url)
            except Exception:
                pass
        if data is None:
            data = Data(
                video_page_url=self.src,
                rtsp_url=rtsp_url
            )
        time.sleep(sleep_time)
        if camera is None or camera.error:
            data.rtsp_url = 'There has been an ERROR while processing the video stream.'
        elif camera is not None and not camera.error:
            data.rtsp_url = camera.rtsp_url
            self.cameras.append(camera)
        return data, camera

    def init_cameras(self) -> List[ThreadedCameraStream]:
        for data in self.found_data:
            self.init_camera(data)
        return self.cameras


def find_videos_in_url_list(src_list: List[str]) -> Dict[str, Scraper]:
    videos_urls = {}
    for src in src_list:
        scraper = Scraper(src)
        videos_urls[scraper.src] = {}
        found_urls = scraper.find_video_links_on_page()
        found_video_sources = scraper.find_video_source_on_page(found_urls)
        scraper.found_data = found_video_sources
        videos_urls[scraper.src] = scraper
        scraper.browser.quit()
    return videos_urls


if __name__ == '__main__':
    vids = find_videos_in_url_list(['http://www.insecam.org/en/bycountry/US/', 'https://lookcam.com/search/?t=traffic'])
    # vids = find_videos_in_url_list(['http://www.insecam.org/en/bycountry/US/'])
    # vids = find_videos_in_url_list(['https://lookcam.com/search/?t=traffic'])
    print(vids)
