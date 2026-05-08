from selenium import webdriver
import bs4
import requests
import json
from datetime import datetime
import pytz
import time
import pandas as pd


#==========================================================
# Facebook Tokens
#==========================================================
def get_user_token(
    username,
    password,
    visual=False,
    driver_path='/usr/local/share/chromedriver',
):
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------
    if visual == False:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(driver_path, chrome_options=options)
    else:
        browser = webdriver.Chrome(driver_path)
    GraphAPIExplorer = 'https://developers.facebook.com/tools/explorer'
    browser.get(GraphAPIExplorer)
    login = browser.find_element_by_link_text('Log In')
    login.click()
    email = browser.find_element_by_name('email')
    email.send_keys(username)
    pwrd = browser.find_element_by_name('pass')
    pwrd.send_keys(password)
    login = browser.find_element_by_name('login')
    login.click()
    page = bs4.BeautifulSoup(browser.page_source, 'lxml')
    browser.quit()
    token_element = [item for item in page.select('input[type="text"]')
        if 'placeholder' in item.attrs
        and 'Access Token' in item['placeholder']]
    token = token_element[0]['value']
    return token


def get_authorized_accounts(token):
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------
    next_url = 'https://graph.facebook.com/me/accounts?access_token=' + token
    continue_paging = True
    data = []
    while continue_paging:
        req = json.loads(requests.get(next_url).text)
        data += req['data']
        try:
            next_url = req['paging']['next']
        except:
            continue_paging = False
    return data


class fb_token():
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------
    def __init__(self, username, password, me='user', version='v2.12'):
        self.username = username
        self.password = password
        self.user_token = get_user_token(username, password)
        accounts = get_authorized_accounts(self.user_token)
        self.accounts = accounts
        self.page_to_token = {item['name'].lower(): item['access_token']
                for item in accounts}
        self.id_to_token = {item['id'].lower(): item['access_token']
                for item in accounts}
        self.page_to_token['user'] = self.user_token
        self.version = version
        self.fbg = 'https://graph.facebook.com/' + self.version + '/'
        self.me = me
        self.active_token = self.page_to_token[me.lower()]

    def renew(self):
        self.__init__(self.username, self.password, self.me)

    def get(self, url, me=None):
        if me is None:
            access_token = self.active_token
        else:
            access_token = self.page_to_token[me.lower()]
        if url.find('?') > 0:
            url = self.fbg + url + '&access_token=' + access_token
        else:
            url = self.fbg + url + '?access_token=' + access_token
        return json.loads(requests.get(url).text)

    def change_token_by_name(self, page_name):
        page_name = page_name.lower()
        if page_name in self.page_to_token.keys():
            self.active_token = self.page_to_token[page_name]
        else:
            assert False, \
                'Oops: Page name is not listed in self.page_to_token.keys()'

    def change_token_by_id(self, page_id):
        try:
            self.active_token = self.id_to_token[page_id]
        except:
            assert False, \
                'Oops: You do not have rights for the given Page ID'

    def change_version(self, version):
        version = version.lower()
        if len(version.split('v')) == 1:
            version = 'v' + version
        if len(version.split('.')) != 2:
            print('Oops: Version must be vx.y, e.g., v2.12')
        try:
            int(''.join(version.split('v')[1].split('.')))
        except:
            print('Oops: Version must be vx.y, where x and y are integer characters,'
                  'e.g., v2.12')
        self.version = version
        self.fbg = 'https://graph.facebook.com/' + version + '/'


#==========================================================
# Facebook Live Streams / Video
#==========================================================
def get_video_ids(token):
    """
    Grabs the live video broadcast ID for a given page token object,
    assuming there is a broadcast currently live (and that there is only
    one such broadcast). Uses the live video ID to obtain the corresponding
    video ID.

    Note: To begin the pipeline before the event starts, look for a
    broadcast with status.lower() == 'scheduled_unpublished'.
    """
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------

    # Video Broadcasts
    video_broadcasts = token.get('me/video_broadcasts')

    # LIVE or SCHEDULED_UNPUBLISHED
    live_videos = [item for item in video_broadcasts['data']
            if item['status'].lower() == 'live'][0]

    # Get video_id from live_id
    if len(live_videos) > 0:
        live_id = live_videos['id']
        response = token.get(live_id + '?fields=video')
        video_id = response['video']['id']
    else:
        video_id = None

    return live_id, video_id


def get_live_views(token, live_id):
    response = token.get(live_id + '?fields=live_views')
    live_views = response['live_views']
    return live_views


#--------SENTINEL-------------
def sentinel(
    token,
    live_id,
    hard_cutoff_time=None,
    cadence=60,
    delay=600,
):
    """
    Monitors a Facebook live stream until it transitions to VOD, then waits
    `delay` seconds before yielding control back to the main pipeline.

    max_observations caps total watch time at 3 hours (w/ cadence=60).

    delay: seconds to wait after stream ends before data collection begins;
      defaults to 10 minutes (600s) to allow metrics to stabilize.

    hard_cutoff_time: for broadcasts where the live node does not reliably
      deactivate when the stream ends, a hard cutoff time (e.g., the known
      scheduled end time) can be specified as 'YYYY-MM-DD HH:MM:SS'.
    """
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------

    print("\nMonitoring Facebook live stream...")
    max_time         = 3 * 3600  # 3 hours
    max_observations = int(max_time / cadence)

    if hard_cutoff_time is not None:
        hard_cutoff_time = datetime.strptime(hard_cutoff_time, '%Y-%m-%d %H:%M:%S')

    i = 0
    while i < max_observations:
        time.sleep(cadence)
        observation = get_live_views(token, live_id)
        now = datetime.strptime(
            datetime.now(
                pytz.timezone('US/Eastern')
            ).strftime('%Y-%m-%d %H:%M:%S'),
            '%Y-%m-%d %H:%M:%S')

        print('now', now.strftime('%Y-%m-%d %H:%M:%S'))
        print('hard_cutoff', hard_cutoff_time)
        print('')
        if observation is None:
            print("\nFacebook live video stream has ended...")
            break
        elif (hard_cutoff_time is not None) and (now > hard_cutoff_time):
            print("\nHard cutoff time exceeded...")
            break
        else:
            i += 1

    end_time = datetime.now(pytz.timezone('EST')).strftime('%H-%M-%S')
    print(f"\nWaiting {delay} seconds before data collection begins...\n")
    time.sleep(int(delay))
    return end_time


def get_video_insights(token, video_id):
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------
    video_insights = token.get(video_id + '/video_insights')
    return video_insights['data']


#==========================================================
# Redshift
#==========================================================
def to_redshift(
    con,
    table,
    event_name,
    event_date,
    brand,
    video_insights,
    fb_id=None,
):
    #-----------------------------
    # Written by: Kevin Urban
    #-----------------------------
    views = [item for item in video_insights
        if item['name'] == 'total_video_views'][0]['values'][0]['value']
    milliseconds = [item for item in video_insights
        if item['name'] == 'total_video_view_total_time'][0]['values'][0]['value']
    mins = round(milliseconds / 60000)
    if fb_id is None:
        fb_id = 'NULL'
    con.execute(f"""
        UPDATE busgrp.{table}
        SET fb_total_3s_views={views},
            fb_total_view_time_minutes={mins},
            fb_id={fb_id}
        WHERE event_name='{event_name}'
          AND event_date='{event_date}'
          AND brand='{brand}'
    """)
