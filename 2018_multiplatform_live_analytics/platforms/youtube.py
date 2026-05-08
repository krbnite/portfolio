import sys
import os
import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from pyvirtualdisplay import Display


def download_csv_file(
    event_dir,
    okta_email,
    okta_password,
    filter_word='kickoff',
    channel='default',
    driver_path='/usr/local/share/chromedriver',
    visual=True,
):
    #--------------------------------
    # Written by: Kevin Urban
    #--------------------------------

    channel = channel.lower()

    # Set dldir to event directory
    #  -- sys.path[0] if Cron
    #  -- os.getcwd() if calling from project directory
    download_directory = sys.path[0]
    if download_directory == '':
        download_directory = os.getcwd()
    download_directory += '/' + event_dir

    display = Display(visible=0)
    display.start()
    prefs = {"download.default_directory": download_directory}
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    capabilities = options.to_capabilities()

    driver = webdriver.Chrome(driver_path, desired_capabilities=capabilities)
    driver.implicitly_wait(20)

    driver.get("https://www.youtube.com/analytics")
    time.sleep(2)
    email_field = driver.find_element_by_id("identifierId")
    time.sleep(1)
    email_field.send_keys(okta_email)
    next_button = driver.find_element_by_id("identifierNext")
    next_button.click()
    time.sleep(2)

    # NOW @ OKTA SCREEN
    okta = driver.current_url.split('.')[1]
    time.sleep(1)
    if okta == 'okta':
        okta_email_field = driver.find_element_by_id("okta-signin-username")
        okta_email_field.send_keys(okta_email)
        time.sleep(1)
        okta_password_field = driver.find_element_by_id("okta-signin-password")
        okta_password_field.send_keys(okta_password)
        time.sleep(1)
        okta_signin = driver.find_element_by_id("okta-signin-submit")
        okta_signin.click()
        time.sleep(1)

    #----------------------------------------------
    # NOTE (2018-06-14)
    #----------------------------------------------
    # YouTube changed how we get signed in: instead of an options screen
    #   listing various channel options, it signs in to the default account
    #   automatically. The commented code below handled the channel-selection
    #   screen; if that screen returns in the future, this may work again.
    #identities = driver.find_elements_by_class_name('identity-prompt-account-public-name')
    #time.sleep(2)
    #[item for item in identities if item.text.lower()==channel][0].click()
    #time.sleep(2)
    #driver.find_elements_by_css_selector('button[class="yt-uix-button yt-uix-button-size-default yt-uix-button-primary"]')[0].click()
    #time.sleep(2)

    driver.get("https://www.youtube.com/my_live_events?filter=completed")
    time.sleep(2)

    all_completed_broadcasts = driver.find_elements_by_class_name('vm-video-item')
    time.sleep(2)

    most_recent_event = [item for item in all_completed_broadcasts
            if filter_word in item.text.lower()][0].find_elements_by_tag_name('button')
    time.sleep(2)

    download_button = [button for button in most_recent_event
                          if button.text.lower() == 'download report'][0]
    time.sleep(2)

    try:
        # NOTE: Could not figure out why, but the first click() ALWAYS
        #   fails. Tried 20-30 second time.sleeps before it, increased the
        #   driver.implicitly_wait up to the same... Still, first click
        #   always failed. Likewise, the second click seems to never
        #   fail.  No idea why.  But... There you have it!  That's why
        #   there are two try/except statements here.
        download_button.click()
        time.sleep(2)
        mission_status = True
    except:
        try:
            download_button.click()
            time.sleep(2)
            mission_status = True
        except:
            print('Both attempts to download CSV file failed.')
            mission_status = False

    driver.close()
    display.stop()

    return mission_status


def extract_data_from_csv(event_dir):
    #--------------------------------
    # Written by: Kevin Urban
    #--------------------------------

    # Set path to event directory
    #  -- sys.path[0] if Cron
    #  -- os.getcwd() if calling from project directory
    path = sys.path[0]
    if path == '':
        path = os.getcwd()
    path += '/' + event_dir

    filename = [item for item in os.listdir(path) if item[:13] == 'youtube_stats'][0]
    youtube_id = filename.split('_')[-1][:-4]

    with open(path + '/' + filename, 'r') as f:
        lines = f.readlines()

    #------------------------------------------
    # Global Numbers
    #------------------------------------------
    # NOTE: This code extracts all global data, but ultimately we only use
    #     total_playbacks and total_mins_watched in the Live Event Report.
    #     Leaving full code here in case someone needs to copy-and-paste it
    #     for a more complete data perspective.
    for jdx, ln in enumerate(lines):
        arr = ln.split(',')
        if arr[0].lower() == 'playbacks':
            arr2 = lines[jdx + 1].split(',')
            total_playbacks        = [int(round(float(arr2[0])))]
            peak_concurrents       = [int(round(float(arr2[1])))]
            total_playback_minutes = [int(round(float(arr2[2]) * 60, 1))]
            avg_mins_watched       = [int(round(float(arr2[3])))]
            break

    #------------------------------------------
    # Country Numbers
    #------------------------------------------
    # NOTE: This code extracts all country data, but ultimately we only
    #     use the US data for playbacks.
    for jdx, ln in enumerate(lines):
        arr = ln.split(',')
        if arr[0].lower().split(' ')[0] == 'country':
            code = arr
            code_data = [item.strip() for item in code[1:]]
            playbacks = lines[jdx + 1].split(',')
            playbacks_data = [int(float(item.strip()))
                    for item in playbacks[1:]]
            peak_currents = lines[jdx + 2].split(',')
            peak_currents_data = [int(float(item.strip()))
                    for item in peak_currents[1:]]
            hrs_viewed = lines[jdx + 3].split(',')
            hrs_viewed_data = [round(float(item.strip()) * 60, 1)
                    for item in hrs_viewed[1:]]
            avg_mins = lines[jdx + 4].split(',')
            avg_mins_data = [round(float(item.strip()), 1)
                    for item in avg_mins[1:]]
            country_data = pd.DataFrame({
                'country_code': code_data,
                'playbacks': playbacks_data,
                'peak_concurrents': peak_currents_data,
                'total_mins_watched': hrs_viewed_data,
                'avg_mins_watched': avg_mins_data
            }, columns=[
                'country_code',
                'playbacks', 'peak_concurrents', 'total_mins_watched',
                'avg_mins_watched'
            ])
            break

    playbacks_us = [int(country_data[country_data.country_code == 'US'].playbacks)]

    ko_data = pd.DataFrame({
        'playbacks': total_playbacks,
        'playbacks_us': playbacks_us,
        'playback_minutes': total_playback_minutes,
        'youtube_id': youtube_id,
    })
    return ko_data


#==========================================================
# Redshift
#==========================================================
def to_redshift(
    con,
    table,
    event_name,
    event_date,
    brand,
    youtube_data,
):
    #--------------------------------
    # Written by: Kevin Urban
    #--------------------------------
    yt_live_playbacks        = youtube_data['playbacks'][0]
    yt_live_playbacks_us     = youtube_data['playbacks_us'][0]
    yt_live_playback_minutes = youtube_data['playback_minutes'][0]
    yt_live_playbacks_percent_us = \
            round(100 * yt_live_playbacks_us / yt_live_playbacks)
    yt_id = youtube_data['youtube_id'][0]
    con.execute(f"""
        UPDATE busgrp.{table}
        SET yt_live_playbacks={yt_live_playbacks},
            yt_live_playbacks_us={yt_live_playbacks_us},
            yt_live_playbacks_percent_us={yt_live_playbacks_percent_us},
            yt_live_playback_minutes={yt_live_playback_minutes},
            yt_id='{yt_id}'
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand = '{brand}'
    """)
