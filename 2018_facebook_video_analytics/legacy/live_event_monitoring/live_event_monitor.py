"""
Written by Kevin Urban (2018)

Polls live video view counts for a Facebook Page during a live event,
and retrieves post-broadcast video insights when the stream ends.

Usage:
    python live_event_monitor.py <page_token> [--version v2.12]
"""
import argparse
import requests
import json
import time
from datetime import datetime
import pytz
import pandas as pd


def get_live_video_views(token, version='v2.12'):
    fb_graph = 'https://graph.facebook.com/' + version + '/'
    token_param = 'access_token=' + token

    # Video Broadcasts
    response = requests.get(fb_graph + 'me/video_broadcasts?' + token_param)
    video_broadcasts = json.loads(response.text)

    # LIVE or SCHEDULED_UNPUBLISHED
    live_videos = [item for item in video_broadcasts['data']
            if item['status'].lower() in ['live', 'scheduled_unpublished']]

    # Get live view count from the first active broadcast
    if len(live_videos) > 0:
        live_ID_0 = live_videos[0]['id']
        response = requests.get(
            fb_graph + live_ID_0 + '?fields=live_views&' + token_param)
        live_views = json.loads(response.text)['live_views']
    else:
        live_views = None

    timestamp = datetime.now(pytz.timezone('EST')).strftime('%Y-%m-%d %H:%M:%S')
    return pd.DataFrame({'timestamp': [timestamp], 'live_views': [live_views]})


def get_time_series_of_live_video_views(
        token, cadence=60, num_steps=45, version='v2.12'):
    i = 0
    data = []
    while i < num_steps:
        temp = get_live_video_views(token, version)
        data.append(temp)
        print(temp)
        time.sleep(cadence)
        i += 1
    return data


def get_video_insights(token, version='v2.12'):
    # THIS CAN ONLY BE DONE AFTER LIVE ENDS
    fb_graph = 'https://graph.facebook.com/' + version + '/'
    token_param = 'access_token=' + token

    # Video Broadcasts
    response = requests.get(fb_graph + 'me/video_broadcasts?' + token_param)
    video_broadcasts = json.loads(response.text)

    # LIVE or SCHEDULED_UNPUBLISHED
    live_videos = [item for item in video_broadcasts['data']
            if item['status'].lower() in ['live', 'scheduled_unpublished']]

    # Get video_id from live_id
    live_ID_0 = live_videos[0]['id']
    response = requests.get(
        fb_graph + live_ID_0 + '?fields=video&' + token_param)
    video_id = json.loads(response.text)['video']['id']

    # Video Insights
    response = requests.get(
        fb_graph + video_id + '/video_insights?' + token_param)
    video_insights = json.loads(response.text)

    return video_insights


if __name__ == '__main__':
    #---------------------------------------------------
    # Command Line Arguments
    #---------------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'token',
        help='Page token for the live event page.',
    )
    parser.add_argument(
        '-v', '--version',
        default='v2.10',
    )

    #---------------------------------------------------
    # Chosen Parameters
    #---------------------------------------------------
    args = parser.parse_args()
    token = args.token
    version = args.version

    timestamp = datetime.now(pytz.timezone('EST')).strftime('%Y%m%d-%H%M%S')
    video_insights = get_video_insights(token, version)

    with open('live_event_insights-' + timestamp + '.json', 'w') as f:
        json.dump(video_insights, f)
