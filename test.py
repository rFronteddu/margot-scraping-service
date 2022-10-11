from selenium.webdriver.common.by import By
from scraper import Scraper
import time

src = 'https://lookcam.com/wagrowiec-panorama-of-town/'
scrap = Scraper(src)
browser = scrap.init_browser()

browser.get(src)
a = browser.page_source
scrap.remove_site_cookies_popup()
res = browser.find_elements(By.XPATH, "//*[contains(.,'52.8067972')]")
for r in res:
    print(r.text)

