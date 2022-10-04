from selenium.webdriver.common.by import By
from scraper import Scraper
import time

src = 'https://lookcam.com/wagrowiec-panorama-of-town/'
scrap = Scraper(src)
browser = scrap.init_browser()

browser.get(src)
scrap.remove_site_cookies_popup()
res = browser.find_elements(By.XPATH, "//*[contains(.,'Wągrowiec (Poland)')]")
for r in res:
    print(r.text)

