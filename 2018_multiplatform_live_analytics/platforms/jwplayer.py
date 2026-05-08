"""
JW Player Selenium scraper for live event video plays and watch time.

NOTE: This was the original planned DotCom platform module, superseded by
Conviva real-time queries (dotcom.py) before the pipeline shipped. Kept as
a reference for the Selenium-based JWP approach.

Credentials required: JWP_EMAIL, JWP_PASSWORD (via .env)
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.phantomjs.service import Service as PhantomService
import re
import time
import pandas as pd
from datetime import datetime
import pytz


def get_data(
    email,
    password,
    livestream_link_text,
    ymd=str(datetime.now(pytz.timezone('US/Eastern'))).split()[0],
    visual=True,
    close=True,
    driver_path='/usr/local/share/chromedriver',
):
    if visual:
        service = ChromeService(driver_path)
    else:
        driver_path = '/usr/local/bin/phantomjs'
        service = PhantomService(driver_path)
    service.start()
    driver = webdriver.Remote(service.service_url, {})

    # Login Page
    driver.get('https://dashboard.jwplayer.com')
    email_field    = driver.find_element_by_name("email")
    password_field = driver.find_element_by_name("password")
    submit_button  = driver.find_elements_by_id("submit_login")[0]
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    time.sleep(2)

    # Content Analytics Page — navigate to today's data for the livestream
    main = "https://dashboard.jwplayer.com/#/analytics/content?"
    url = (main +
           'pageLength=l' +
           '&dateRange=custom' +
           '&dateRangeEnd=' + ymd +
           '&dateRangeStart=' + ymd +
           '&page=1')
    driver.get(url)
    time.sleep(2)

    livestream = driver.find_element_by_link_text(livestream_link_text)
    livestream.click()
    time.sleep(2)

    # Live Streams — total plays
    # NOTE: this was throwing errors intermittently
    tot_plays_tag = driver.find_element_by_class_name("total-plays")
    time.sleep(1)
    tot_plays = int(''.join(tot_plays_tag.text.split("\n")[1].split(",")))

    # % US
    us_pc_tag = driver.find_element_by_class_name("country")
    time.sleep(1)
    us_pc = us_pc_tag.text.split("\n")[1]
    us_pc_dec = float(us_pc.split("%")[0]) / 100.

    us_tot_plays = us_pc_dec * tot_plays

    # Total Time Watched
    data_legend = driver.find_element_by_class_name("chart-line-legend")
    time.sleep(1)
    hh_mm = data_legend.text.split("\n")[0].split(":")
    mins_watched = (int(''.join(hh_mm[0].split(','))) * 60 +
                    int(''.join(hh_mm[1].split(','))))

    if close:
        driver.quit()

    return tot_plays, us_tot_plays, us_pc, mins_watched


def test(
    email,
    password,
    driver_path='/usr/local/share/chromedriver',
    visual=True,
):
    """
    Scrapes the JWP content analytics table for today and returns a DataFrame.
    NOTE: This worked interactively but not when called as jwp.test() — root
    cause was never fully diagnosed before JWP was superseded by Conviva.
    """
    today = str(datetime.now(pytz.timezone('US/Eastern'))).split()[0]

    if visual:
        service = ChromeService(driver_path)
    else:
        driver_path = '/usr/local/bin/phantomjs'
        service = PhantomService(driver_path)
    service.start()
    driver = webdriver.Remote(service.service_url, {})

    driver.get('https://dashboard.jwplayer.com')
    email_field    = driver.find_element_by_name("email")
    password_field = driver.find_element_by_name("password")
    submit_button  = driver.find_elements_by_id("submit_login")[0]
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    time.sleep(2)

    main = "https://dashboard.jwplayer.com/#/analytics/content?"
    url = (main +
           'pageLength=l' +
           '&dateRange=custom' +
           '&dateRangeEnd=' + today +
           '&dateRangeStart=' + today +
           '&page=1')
    driver.get(url)
    time.sleep(2)

    tables = driver.find_elements_by_tag_name('table')
    # In experiment, 3 tables were found; data was in the last table
    rows = tables[-1].text.split('\n')

    columns = re.sub('complete rate', 'complete_rate', rows[0].lower())
    columns = re.sub('time watched', 'time_watched', columns)
    columns = (columns + ' time_units').split()

    df = pd.DataFrame(columns=columns)
    for idx, row in enumerate(rows[1:], 1):
        split1 = re.split(' Video ', row)
        title = split1[0]
        right_cols = [int(re.sub(',|%', '', col))
                if (col != 'hours' and col != 'minutes') else col
                for col in split1[1].split()]
        title_splitter = re.sub(r'\?', r'\\?', title)
        title_splitter = re.sub(r'\)', r'\\)', title_splitter)
        title_splitter = re.sub(r'\(', r'\\(', title_splitter)
        content_type = re.split(title_splitter, row)[1].split()[0]
        df.loc[idx] = [title] + [content_type] + right_cols

    return df
