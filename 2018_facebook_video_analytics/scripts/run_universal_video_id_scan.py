#!/usr/bin/env python
"""
Written by Kevin Urban (2018)

Scans all authorized Facebook Pages for videos that have a universal_video_id
field set, since a given date.  Outputs a CSV with basic performance metrics
alongside the universal video ID for cross-platform matching.
"""
import argparse
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.graph_api import fb_token

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--since',
        default='2018-06-01',
        help='Scan for videos published since this date (YYYY-MM-DD).',
    )
    parser.add_argument(
        '--output',
        default='videos_with_universal_video_id.csv',
        help='Output CSV filename.',
    )
    args = parser.parse_args()

    username = os.getenv('FB_USERNAME')
    password = os.getenv('FB_PASSWORD')

    token = fb_token(username, password)
    pages = list(token.id_to_token.keys())

    # NOTE:
    # length is given in seconds (minutes: time/60)
    # total time watched is given in milliseconds (minutes: time/60000)
    df = pd.DataFrame(columns=[
        'fbid', 'universal_video_id', 'title', 'length_mins',
        'total_video_views', 'total_mins_watched',
    ])
    for page in pages:
        token.change_token_by_id(page)
        data = token.get(
            f'me?fields=videos.since({args.since}).limit(1000){{'
            'id,universal_video_id,title,length,video_insights.metric('
            'total_video_views,total_video_view_total_time'
            ')}'
        )
        if 'videos' in data.keys():
            data = data['videos']['data']
            uid = [{'fbid': video['id'],
                    'universal_video_id': video['universal_video_id'],
                    'title': video['title'],
                    'length_mins': video['length'] / 60,
                    'total_video_views': video['video_insights']['data'][0]['values'][0]['value'],
                    'total_mins_watched': video['video_insights']['data'][1]['values'][0]['value'] / 60000,
            } for video in data if 'universal_video_id' in video.keys()]
            df = df.append(pd.DataFrame(uid), ignore_index=True)

    df.to_csv(args.output, index=False)
    print(f'Saved {len(df)} videos to {args.output}')
