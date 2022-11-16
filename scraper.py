import json
import time
import re

import requests
from selenium import webdriver
from selenium.common import StaleElementReferenceException, NoSuchFrameException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import List, Dict, Tuple
from webdriver_manager.chrome import ChromeDriverManager
from camera import ThreadedCameraStream
from model import Data, CameraHolder, GeolocationModel

sleep_time = 0.5

page_title_cleanse_things = ["camera", "live", "webcam", "cam", ":", "-", ".", ",", '&']
geolocation_aliases = {'latitude': ['latitude', 'lt'],
                       'longitude': ['longitude', 'ln'],
                       'locality': ['locality', 'place'],
                       'city': ['city', 'town'],
                       'region': ['region', 'state'],
                       'country': ['country']
                       }
location_delimiters = ['-', ':']

geocoding_api_url = 'http://dev.virtualearth.net/REST/v1/Locations/{query}?maxRes=3&key={key}'
geocoding_api_key = 'AqVzpN0yLUp3VvWccG02Hklgt6L5LYVWnAcFTIWWg-7IkLqLm3Man_Rl2skFRzDp'


class Scraper:
    def __init__(self, src: str, direct_video_link: bool = False):
        self.src = src
        self.cameras = []
        self.browser = None
        self.entity_types: list[str] = []
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
        return eval(str(log.get('message')).replace("false", "False").replace("true", "True")).get('message').get('params')

    def validate_found_stream_url(self, url):
        if url is None or url == '':
            return False
        return url.__contains__("hlsplaylist.html") or url.__contains__(".m3u8")

    def get_blob_video_url(self, go_to_page: bool = False, cookies_consent: bool = True) -> str:
        try:
            if self.browser is None:
                self.init_browser()
            if go_to_page:
                self.browser.get(self.src)
            if not cookies_consent:
                self.remove_site_cookies_popup()
            performance_log = self.browser.get_log('performance')
            validated_urls = []
            for i in performance_log:
                response_message_method = json.loads(i.get('message')).get('message').get('method')
                message_params = self.eval_network_message(i)
                if response_message_method == 'Network.requestWillBeSent':
                    url = message_params.get('request').get('url')
                    if self.validate_found_stream_url(url):
                        if url.__contains__("playlist.m3u8"):
                            return url
                        else:
                            validated_urls.append(url)
            if validated_urls.__len__() > 0:
                return validated_urls[0]
        except Exception:
            pass
        return ''

    def find_video_links_on_page(self) -> List[str]:
        videos_urls = []
        self.browser.get(self.src)
        self.remove_site_cookies_popup()
        a_links = self.browser.find_elements(By.TAG_NAME, 'a')
        try:
            for a_element in a_links:
                if a_element.find_element(By.XPATH, '..').tag_name.__eq__('div') and a_element.size['width'] > 100 and a_element.size['height'] > 100 and \
                        (
                            any(child.tag_name == 'img' for child in a_element.find_elements(By.XPATH, './/img')) or
                            a_element.value_of_css_property("background-image") != ""
                        ):
                    videos_urls.append(a_element.get_attribute('href'))
                    print(a_element.get_attribute('href'))
        except Exception as e:
            pass
        return videos_urls

    def contains_number(self, string: str):
        return any(char.isdigit() for char in string)

    def keep_only_numerics_from_string(self, string) -> float:
        return float(re.sub(r'[^0-9|.|,]', '', string))

    def find_element_containing_text(self, search_text) -> WebDriver or None:
        for text in geolocation_aliases[search_text]:
            elem = self.browser.find_elements(By.XPATH, "//*[contains(translate(text(), "
                                                        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                                                        "'abcdefghijklmnopqrstuvwxyz'), '"
                                              + text + "')]")
            for e in elem:
                if e.text != '':
                    return e
        return None

    def extract_present_geolocation_from_page(self, search_text) -> float:
        coords = self.find_element_containing_text(search_text)
        if coords is None or coords.text == '':
            return .0

        if self.contains_number(coords.text):
            numeric_result = self.keep_only_numerics_from_string(coords.text)
            # print(coords.text + ': ' + numeric_result)
            return numeric_result
        else:
            sibling = coords.find_elements(By.XPATH, "following-sibling::*[1]")
            # print(coords.text + ' ' + sibling[0].text)
            try:
                return float(sibling[0].text)
            except ValueError:
                return .0

    def extract_present_location_from_page(self, search_text) -> str:
        location = self.find_element_containing_text(search_text)
        if location is None or location.text == '':
            return ''
        for delim in location_delimiters:
            if location.text.__contains__(delim) and len(search_text) + 2 < len(location.text):
                cleansed_location = location.text.split(delim)[1].rstrip().lstrip()
                # print(location.text + ': ' + cleansed_location)
                return cleansed_location
        else:
            sibling = location.find_elements(By.XPATH, "following-sibling::*[1]")
            # print(location.text + ' ' + sibling[0].text)
            try:
                return sibling[0].text
            except ValueError:
                return ''

    def find_geolocation_from_page_title(self, page_title: str, purge_from_src: bool = True) -> GeolocationModel:
        search_phrase = page_title.lower()
        ulr_to_remove = self.src \
            .replace('https', '') \
            .replace('http', '') \
            .replace('://', '') \
            .replace('www.', '')
        search_phrase = search_phrase \
            .replace(ulr_to_remove, '') \
            .replace(ulr_to_remove.split('.')[0], '')
        for rem in page_title_cleanse_things:
            search_phrase = search_phrase.replace(rem, '')
        search_phrase = re.sub(' +', ' ', search_phrase)
        if purge_from_src:
            remaining_search_words = search_phrase.split(' ')
            removed: list[str] = []
            for word in reversed(remaining_search_words):
                if self.src.__contains__(word) and all(not a.__contains__(word) for a in removed):
                    removed.append(word)
                    search_phrase = search_phrase.replace(word, '')
        search_phrase = re.sub(' +', ' ', search_phrase).rstrip().lstrip()
        print('Seach phrase: ' + search_phrase)
        response = requests.get(geocoding_api_url.format(query=search_phrase, key=geocoding_api_key))
        final_geolocation = GeolocationModel()
        if response.status_code == 200:
            response_resources = response.json()['resourceSets'][0]['resources']
            found_locations: list[GeolocationModel] = []
            for i in range(len(response_resources)):
                geolocation = GeolocationModel()
                response_resource = response_resources[i]
                coords = response_resource['point']['coordinates']
                geolocation.latitude = coords[0]
                geolocation.longitude = coords[1]
                geolocation.entity_type = response_resource['entityType']
                if page_title.replace(' ', '').lower().__contains__(str(geolocation.entity_type).lower()) and not self.entity_types.__contains__(geolocation.entity_type):
                    self.entity_types.append(geolocation.entity_type)
                response_address = response_resource['address']
                try:
                    geolocation.country = response_address['countryRegion']
                    geolocation.city = response_address['adminDistrict2']
                    geolocation.place = response_address['locality']
                except KeyError:
                    pass
                found_locations.append(geolocation)
            for location in found_locations:
                for entity_type in self.entity_types:
                    if location.entity_type == entity_type:
                        final_geolocation = location
            if len(found_locations) >= 1 and final_geolocation.latitude == .0 or final_geolocation.country == '':
                final_geolocation = found_locations[0]
        else:
            print(response.status_code)
        return final_geolocation

    def find_geolocation(self, page_title: str, purge_from_src: bool = True) -> GeolocationModel:
        latitude = self.extract_present_geolocation_from_page("latitude")
        longitude = self.extract_present_geolocation_from_page("longitude")
        geo = GeolocationModel()
        if latitude != .0 or longitude != .0:
            geo.latitude = latitude
            geo.longitude = longitude
            # locality = self.extract_present_location_from_page("locality")
            city = self.extract_present_location_from_page("city")
            region = self.extract_present_location_from_page("region")
            country = self.extract_present_location_from_page("country")
            # if locality != '':
            #     geo.place = locality
            if city != '':
                geo.city = city
            if region != '':
                geo.country = region
            if country != '':
                if geo.country == '':
                    geo.country = country
                else:
                    geo.country += ', ' + country
        else:
            geo = self.find_geolocation_from_page_title(page_title, purge_from_src)
        return geo

    def create_data(self, scrap_page_url: str, video_url: str, stream_url: str, location: GeolocationModel) -> Data:
        return Data(
            scraped_page_url=scrap_page_url,
            video_page_url=video_url,
            rtsp_url=stream_url,
            latitude=location.latitude,
            longitude=location.longitude,
            country=location.country,
            city=location.city,
            place=location.place
        )

    def move_to_elements_and_get_src(self, elements, video_element):
        video_src = ''
        for element in elements:
            try:
                ActionChains(self.browser).move_to_element(element).click(element).perform()
                video_src = video_element.get_attribute('src')
                if video_src != '':
                    return video_src
            except Exception:
                pass
        return video_src

    def find_and_click_button_and_divs_to_play_video_element(self, video_element, current_element, depth: int):
        parent_to_search = video_element.find_element(By.XPATH, '..') if current_element is None else current_element.find_element(By.XPATH, '..')
        while depth > 1:
            parent_to_search = parent_to_search.find_element(By.XPATH, '..')
            depth = depth - 1
        buttons = parent_to_search.find_elements(By.XPATH, './/button')
        divs = parent_to_search.find_elements(By.XPATH, './/div')
        video_src = self.move_to_elements_and_get_src(buttons, video_element)
        if video_src == '':
            video_src = self.move_to_elements_and_get_src(divs, video_element)
        return video_src

    def find_videos_source_in_frame(self, elements: list[WebElement], src: str, url: str) -> List[Data]:
        videos_urls: list[Data] = []
        try:
            for element in elements:
                if element.size['width'] >= 10 and element.size['height'] >= 10:
                    video_src = element.get_attribute('src')
                    if video_src == '' or video_src is None:
                        video_src = self.find_and_click_button_and_divs_to_play_video_element(element, None, 3)
                        time.sleep(sleep_time)
                    got_src_from_child = False
                    if video_src is None or video_src == '' or video_src.startswith("blob:"):
                        video_children = element.find_elements(By.XPATH, './/*')
                        for child in video_children:
                            child_src = child.get_attribute('src')
                            if child_src is not None and child_src != '':
                                location = self.find_geolocation(self.browser.title, self.src != url)
                                videos_urls.append(self.create_data(src, url, child_src, location))
                                got_src_from_child = True
                    if video_src is not None and video_src != '' and not got_src_from_child:
                        pure_video_source = video_src if not video_src.__contains__('blob') else self.get_blob_video_url()
                        location = self.find_geolocation(self.browser.title, self.src != url)
                        videos_urls.append(self.create_data(src, url, pure_video_source, location))
        except Exception as e:
            pass
        return videos_urls

    def find_video_source_on_page(self, src: str, url_list: List[str]) -> List[Data]:
        videos_urls = []
        for url in url_list:
            self.browser.get(url)
            time.sleep(sleep_time)
            found_videos: list[Data] = self.find_videos_source_in_frame(self.browser.find_elements(By.TAG_NAME, 'video'), src, url)
            for data in found_videos:
                videos_urls.append(data)
            if len(found_videos) == 0:
                iframes: list[WebElement] = self.browser.find_elements(By.XPATH, '//iframe')
                for iframe in iframes:
                    try:
                        width = iframe.get_attribute('width').replace('%', '').replace('px', '').replace(' ', '').replace(':', '')
                        height = iframe.get_attribute('height').replace('%', '').replace('px', '').replace(' ', '').replace(':', '')
                        if not width.isnumeric() or not height.isnumeric():
                            continue
                        if not iframe.get_attribute('src').__contains__('google') and int(height) > 100 and int(width) > 100:
                            self.browser.switch_to.frame(iframe)
                            frame_videos: list[WebElement] = self.browser.find_elements(By.TAG_NAME, 'video')
                            for iframe_video in self.find_videos_source_in_frame(frame_videos, src, url):
                                videos_urls.append(iframe_video)
                            self.browser.switch_to.default_content()
                    except Exception:
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
            data = Data(scraped_page_url=self.src, video_page_url=self.src, rtsp_url=rtsp_url)
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
    try:
        for src in src_list:
            scraper = Scraper(src)
            videos_urls[scraper.src] = {}
            found_video_sources = scraper.find_video_source_on_page(src, [src])
            if found_video_sources.__len__() == 0:
                found_urls = scraper.find_video_links_on_page()
                found_video_sources = scraper.find_video_source_on_page(src, found_urls)
            scraper.found_data = found_video_sources
            videos_urls[scraper.src] = scraper
            scraper.browser.quit()
    except Exception:
        pass
    return videos_urls
