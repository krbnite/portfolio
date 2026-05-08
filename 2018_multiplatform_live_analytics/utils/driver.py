from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.phantomjs.service import Service as PhantomService


def get_driver(
    visual=True,
    driver_path='/usr/local/share/chromedriver',
):
    if visual:
        service = ChromeService(driver_path)
    else:
        service = PhantomService('/usr/local/bin/phantomjs')
    service.start()
    driver = webdriver.Remote(service.service_url, {})
    return driver
