import pandas as pd
import time
import os
import datetime
import urllib.request
from urllib.parse import urljoin
from selenium import webdriver
from pyvirtualdisplay import Display


def get_data(event_dir, user, password):

    # Windows or Linux
    if os.name == "posix":
        display = Display(visible=0, size=(800, 600))
        display.start()
        driver_path = "/usr/local/share/chromedriver"
    else:
        driver_path = "C:/Anaconda3/Lib/site-packages/selenium/webdriver/chrome/chromedriver"

    now = datetime.datetime.now()
    ppv_name = event_dir + \
            f"/twitter__{now.month}-{now.day}-{now.hour}-{now.minute}-{now.minute}.csv"

    driver = webdriver.Chrome(driver_path)
    driver.get('https://www.periscope.tv/account/analytics')
    time.sleep(4)

    login2 = driver.find_elements_by_class_name("is-secondary")
    login2[0].click()
    time.sleep(4)

    login3 = driver.find_element_by_class_name("SignInModalRevamp-twitter")
    login3.click()
    time.sleep(4)

    new_handle = driver.window_handles[1]
    driver.switch_to_window(new_handle)
    time.sleep(2)

    username = driver.find_element_by_id("username_or_email")
    username.send_keys(user)

    time.sleep(2)
    pswd = driver.find_element_by_id("password")
    pswd.send_keys(password)

    submit = driver.find_element_by_id("allow")
    submit.click()
    time.sleep(4)

    driver.switch_to_window(driver.window_handles[-1])
    exp = driver.find_elements_by_class_name("ButtonWithIcon")
    exp[5].click()

    csv_url = urljoin(
        "https://www.periscope.tv/account/analytics",
        driver.\
            find_element_by_class_name("AccountStats-downloadLink").\
            get_attribute("href")
    )
    urllib.request.urlretrieve(csv_url, ppv_name)
    driver.quit()

    if os.name == "posix":
        display.stop()

    data = pd.read_csv(ppv_name)
    return data


def get_live_viewers(data):
    return int(data.loc[0][5])


def get_live_vod_viewers(data):
    return int(data.loc[0][4])


def to_redshift_live(
    conn,
    table,
    event_name,
    event_date,
    brand,
    twt_live_viewers,
):
    conn.execute(f"""
        UPDATE busgrp.{table}
        SET twt_live_viewers={twt_live_viewers}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand='{brand}'
    """)


def to_redshift_live_vod(
    conn,
    table,
    event_name,
    event_date,
    brand,
    twt_viewers,
):
    """
    For use with the live + VOD report (content_kickoff_report_live_plus_vod).
    """
    conn.execute(f"""
        UPDATE busgrp.{table}
        SET twt_viewers={twt_viewers}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand='{brand}'
    """)
