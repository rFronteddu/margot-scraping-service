import json
import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager


class Scraper:
    def __init__(self, src=''):
        self.browser = self.init_browser()
        self.src = src

    def init_browser(self):
        chrome_options = Options()
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "download.default_directory": r"/Users/khertys/Downloads/ihmc",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                desired_capabilities=desired_capabilities,
                                options=chrome_options)

    def get_blob_video_url(self):
        try:
            self.browser.get(self.src)
            cookies_elem = self.browser.find_elements(By.CLASS_NAME, "css-47sehv")
            if cookies_elem.__len__() > 0:
                cookies_elem[0].click()
            time.sleep(1)
            class_players = self.browser.find_elements(By.CLASS_NAME, "player")
            if class_players.__len__() > 0:
                class_players[0].click()
            else:
                tag_players = self.browser.find_elements(By.TAG_NAME, "player")
                if tag_players.__len__() > 0:
                    tag_players[0].click()
                else:
                    id_players = self.browser.find_elements(By.ID, "player")
                    if id_players.__len__() > 0:
                        id_players[0].click()
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
                    print(path)
                    if path:
                        find_content = str(path).__contains__("hlsplaylist.html") or str(path).__contains__("m3u8")
                        if find_content:
                            authority = headers.get(':authority')
                            scheme = headers.get(':scheme')
                            return scheme + '://' + authority + path
            print()
        except Exception as e:
            print(e)
            pass
        except NoSuchElementException:
            pass
        finally:
            self.browser.quit()
