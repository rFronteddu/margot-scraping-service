import json
import time
import re

import requests
from selenium import webdriver
from selenium.common import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import List, Dict, Tuple
from webdriver_manager.chrome import ChromeDriverManager
from camera import ThreadedCameraStream
from model import Data, CameraHolder, GeolocationModel

sleep_time = 0.5

page_title_cleanse_things = ["camera", "live", "webcam", "cam", ":", "-", ".", ","]
geolocation_aliases = {'latitude': ['latitude', 'lt'],
                       'longitude': ['longitude', 'ln']
                       }

geocoding_api_url = 'http://dev.virtualearth.net/REST/v1/Locations/{query}?maxRes=1&key={key}'
geocoding_api_key = 'AqVzpN0yLUp3VvWccG02Hklgt6L5LYVWnAcFTIWWg-7IkLqLm3Man_Rl2skFRzDp'


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
        # chrome_options.headless = True //later uncomment for production usage
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        # self.browser = webdriver.Remote(command_executor="http://selenium:4444/wd/hub",
        #                                desired_capabilities=desired_capabilities,
        #                                options=chrome_options)
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager(version='106.0.5249.21').install()),
                                        desired_capabilities=desired_capabilities,
                                        options=chrome_options)
        self.browser.set_page_load_timeout(30)
        return self.browser

    def remove_site_cookies_popup(self):
        time.sleep(sleep_time)
        if len(self.browser.find_elements(By.CLASS_NAME, "css-47sehv")) > 0:
            element = WebDriverWait(self.browser, 2000).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "css-47sehv")))
            element.click()

    def eval_network_message(self, log):
        return eval(str(log.get('message')).replace("false", "False").replace("true", "True")) \
            .get('message').get('params')

    def validate_found_stream_url(self, url):
        if url is None or url == '':
            return False
        return url.__contains__("hlsplaylist.html") or url.__contains__("m3u8")

    def get_blob_video_url(self, go_to_page: bool = False, cookies_consent: bool = True) -> str:
        try:
            if self.browser is None:
                self.init_browser()
            if go_to_page:
                self.browser.get(self.src)
            if not cookies_consent:
                self.remove_site_cookies_popup()
            performance_log = self.browser.get_log('performance')
            for i in performance_log:
                response_message_method = json.loads(i.get('message')).get('message').get('method')
                message_params = self.eval_network_message(i)
                if response_message_method == 'Network.requestWillBeSent':
                    url = message_params.get('request').get('url')
                    if self.validate_found_stream_url(url):
                        return url
        except Exception:
            pass
        return ''

    def find_video_links_on_page(self) -> List[str]:
        videos_urls = []
        self.browser.get(self.src)
        self.remove_site_cookies_popup()
        a_links = self.browser.find_elements(By.TAG_NAME, 'a')
        for a_element in a_links:
            if a_element.find_element(By.XPATH, '..').tag_name.__eq__('div') and \
                    any(
                        child.tag_name == 'img' for child in a_element.find_elements(By.XPATH, './/img')
                    ) and a_element.size['width'] > 100 and a_element.size['height'] > 100:
                videos_urls.append(a_element.get_attribute('href'))
        return videos_urls

    def contains_number(self, string: str):
        return any(char.isdigit() for char in string)

    def keep_only_numerics_from_string(self, string) -> float:
        return float(re.sub(r'[^0-9|.|,]', '', string))

    def find_element_containing_text(self, search_text) -> WebDriver or None:
        for text in geolocation_aliases[search_text]:
            coords = self.browser.find_elements(By.XPATH, "//*[contains(translate(text(), "
                                                          "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                                                          "'abcdefghijklmnopqrstuvwxyz'), '"
                                                + text + "')]")
            if len(coords) > 0:
                return coords[0]
        return None

    def extract_present_geolocation_from_page(self, search_text) -> float:
        coords = self.find_element_containing_text(search_text)
        if coords is None or coords.text == '':
            return .0

        if self.contains_number(coords.text):
            numeric_result = self.keep_only_numerics_from_string(coords.text)
            print(coords.text + ': ' + numeric_result)
            return numeric_result
        else:
            sibling = coords.find_elements(By.XPATH, "following-sibling::*[1]")
            print(coords.text + ' ' + sibling[0].text)
            try:
                return float(sibling[0].text)
            except ValueError:
                return .0

    def find_geolocation_from_page_title(self, page_title: str) -> GeolocationModel:
        search_phrase = page_title.lower()
        ulr_to_remove = self.src\
            .replace('https', '')\
            .replace('http', '')\
            .replace('://', '')\
            .replace('www.', '')
        search_phrase = search_phrase\
            .replace(ulr_to_remove, '')\
            .replace(ulr_to_remove.split('.')[0], '')
        for rem in page_title_cleanse_things:
            search_phrase = search_phrase.replace(rem, '')
        search_phrase = re.sub(' +', ' ', search_phrase)
        remaining_search_words = search_phrase.split(' ')
        removed: list[str] = []
        for word in reversed(remaining_search_words):
            if self.src.__contains__(word) and all(not a.__contains__(word) for a in removed):
                removed.append(word)
                search_phrase = search_phrase.replace(word, '')
        search_phrase = re.sub(' +', ' ', search_phrase).rstrip()
        print(search_phrase)
        response = requests.get(geocoding_api_url.format(query=search_phrase, key=geocoding_api_key))
        geolocation = GeolocationModel()
        if response.status_code == 200:
            coords = response.json()['resourceSets'][0]['resources'][0]['geocodePoints'][0]['coordinates']
            geolocation.latitude = coords[0]
            geolocation.longitude = coords[1]
        else:
            print(response.status_code)
        return geolocation

    def find_geolocation(self, page_title: str) -> GeolocationModel:
        latitude = self.extract_present_geolocation_from_page("latitude")
        longitude = self.extract_present_geolocation_from_page("longitude")
        geo = GeolocationModel()
        if latitude != .0 or longitude != .0:
            geo.latitude = latitude
            geo.longitude = longitude
        else:
            geo = self.find_geolocation_from_page_title(page_title)
        return geo

    def find_video_source_on_page(self, src: str, url_list: List[str]) -> List[Data]:
        videos_urls = []
        for url in url_list:
            self.browser.get(url)
            time.sleep(sleep_time)
            videos = self.browser.find_elements(By.TAG_NAME, 'video')
            for video in videos:
                try:
                    if video.size['width'] < 10 and video.size['height'] < 10:
                        continue
                    location = self.find_geolocation(self.browser.title)
                    video_src = video.get_attribute('src')
                    if video_src is None or video_src == '':
                        video_children = video.find_elements(By.XPATH, './/*')
                        for child in video_children:
                            child_src = child.get_attribute('src')
                            if child_src is not None and child_src != '':
                                videos_urls.append(Data(
                                    scraped_page_url=src,
                                    video_page_url=url,
                                    rtsp_url=child_src,
                                    latitude=location.latitude,
                                    longitude=location.longitude
                                ))
                    if video_src is not None and video_src != '':
                        print(url)
                        pure_video_source = video_src \
                            if not video_src.__contains__('blob') \
                            else self.get_blob_video_url()
                        videos_urls.append(Data(
                            scraped_page_url=src,
                            video_page_url=url,
                            rtsp_url=pure_video_source,
                            latitude=location.latitude,
                            longitude=location.longitude
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
                scraped_page_url=self.src,
                video_page_url=self.src,
                rtsp_url=rtsp_url
            )
        time.sleep(sleep_time)
        if camera is None or camera.error or data.rtsp_url == '':
            data.rtsp_url = 'There has been an ERROR while processing the video stream.'
        elif camera is not None and not camera.error:
            data.rtsp_url = camera.rtsp_url
            self.cameras.append(camera)
        return data, camera

    def init_cameras(self, skip) -> List[ThreadedCameraStream]:
        for data in self.found_data:
            if all(i.data.video_page_url != data.video_page_url for i in skip):
                if not data.rtsp_url.__contains__('m3u8'):
                    self.init_camera(data)
        return self.cameras


def find_videos_in_url_list(src_list: List[str]) -> Dict[str, Scraper]:
    videos_urls = {}
    for src in src_list:
        scraper = Scraper(src)
        videos_urls[scraper.src] = {}
        found_urls = scraper.find_video_links_on_page()
        found_video_sources = scraper.find_video_source_on_page(src, found_urls)
        scraper.found_data = found_video_sources
        videos_urls[scraper.src] = scraper
        scraper.browser.quit()
    return videos_urls


if __name__ == '__main__':
    vids = find_videos_in_url_list(['http://www.insecam.org/en/bycountry/US/', 'https://lookcam.com/search/?t=traffic'])
    # vids = find_videos_in_url_list(['http://www.insecam.org/en/bycountry/US/'])
    # vids = find_videos_in_url_list(['https://lookcam.com/search/?t=traffic'])
    print(vids)
