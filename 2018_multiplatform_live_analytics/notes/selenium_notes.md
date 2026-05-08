
### 1. Get selenium package
```
pip install selenium
```

### 2. Make sure you have Chrome Driver installed

1. Find Chrome Driver at: https://sites.google.com/a/chromium.org/chromedriver/home
2. Download the Desktop driver (at time of this writing):
  - Click on [Getting started with ChromeDriver on Desktop](https://sites.google.com/a/chromium.org/chromedriver/getting-started)
  - Click on [downloads](https://sites.google.com/a/chromium.org/chromedriver/downloads)
  - Click on latest release (currently 2.31)
  - Choose zip file for computer the script will run on (you might have to do this first for your
    development computer, e.g., a Mac or Windows, then again for a production computer)
  - Download zip file to known location (e.g., path/to/Applications/folder)


### 3. In Python
# Example
```python
import time
from selenium import webdriver
import selenium.webdriver.chrome.service as service

service = service.Service('/path/to/chromedriver')
service.start()
capabilities = {'chrome.binary': '/path/to/custom/chrome'}
driver = webdriver.Remote(service.service_url, capabilities)
driver.get('http://www.google.com/xhtml');
time.sleep(5) # Let the user actually see something!
driver.quit()

```

I found that `capabilities` needs to be passed as a 2nd argument to
`webdriver.Remote`, but it can actually be an empty dictionary `{}`.
I think it just finds the Chrome app, period... At least if you have
it installed somewhere in your system's path.


IMPORTANT: Using this webdriver allows the automated control of a
web browser, however if you do not know exactly what IDs or tags to
look for, it will not be extremely helpful (at first). I would
recommend exploring the contents of each page you want to navigate
first using requests and BeautifulSoup.


```python
from selenium import webdriver
import selenium.webdriver.chrome.service as service
service = service.Service('/path/to/chromedriver')
service.start()
driver = webdriver.Remote(service.service_url, {})
driver.get('https://dashboard.jwplayer.com')

# Login Page
## Extract Form Features
email    = driver.find_element_by_name("email")
password = driver.find_element_by_name("password")
submit_button = driver.find_elements_by_id("submit_login")[0]
## Drive Form Features
email.send_keys("your_email@example.com")
password.send_keys("your_password")
submit_button.click()

# Do Stuff
## Switch to active element (e.g., to dismiss a modal dialog)
driver.switch_to_active_element().click()

## Go to a specific page
driver.get("https://dashboard.jwplayer.com/#/analytics/content")

## Refresh browser
driver.refresh()

## Get page source
driver.page_source

## Turn page source into BeautifulSoup object
bs = bs4.BeautifulSoup(driver.page_source,'lxml')

## Take a ScreenShot
driver.get_screenshot_as_file('/path/to/screenshot.png')

## Switching frame might become important...
driver.switch_to_frame
```

We can actually focus on getting the URL right:
```python
main = "https://dashboard.jwplayer.com/#/analytics/content?"
pageLength='s'
dateRange='custom'
dateRangeEnd=ppvDate
dateRangeStart=ppvDate
pages = [i+1 for i in range(10)]
for page in pages:
  url = main+\
    'pageLength='+pageLength+\
    '&dateRange='+dateRange+\
    '&dateRangeEnd='+dateRangeEnd+\
    '&dateRangeStart='+dateRangeStart+\
    '&page='+page
  driver.get(url)
  # get 10 rows of data somehow, e.g., maybe w/ BeautifulSoup
  bs = bs4.BeautifulSoup(driver.page_source,'lxml')
```

NOTE: For some reason exiting python is a chore after using webdriver...
But just wait: it will eventually exit.


https://automatetheboringstuff.com/chapter11/

http://selenium-python.readthedocs.io/locating-elements.html
