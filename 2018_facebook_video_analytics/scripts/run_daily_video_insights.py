#!/usr/bin/env python
"""
Written by Kevin Urban
"""
import argparse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.graph_api import fb_token
from pipelines import daily_video_insights as helper
from utils import s3

current_directory = os.getcwd()

if __name__ == '__main__':
    #-------------------------------------------
    # Command Line Arguments
    #-------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--since',
        default='15 days ago',
        help='Video publish date pastward cut off, e.g., this defaults to tracking a video '
        'for 15 days after it was published/posted.',
    )
    parser.add_argument(
        '--until',
        default=None,
        help='Video publish date futureward cut off; defaults to None (today).',
    )
    parser.add_argument(
        '--page-id',
        default='all',
        help='Comma-separated list of Facebook Page IDs (defaults to all).',
    )
    parser.add_argument(
        '--s3bucket',
        default=os.getenv('S3_BUCKET', ''),
        help='Root name of S3 bucket that data will be pushed to.',
    )
    parser.add_argument(
        '--s3keypath',
        default=os.getenv('S3_KEYPATH', 'facebook/video_insights/'),
        help='Path to "directory" within S3 bucket where data will be stored.',
    )
    parser.add_argument(
        '--not-a-test',
        action='store_true',
        help='Set this flag to insert data into production table. '
             'Default: Data is inserted into a test table.',
    )
    args = parser.parse_args()
    today = datetime.now().strftime('%Y-%m-%d')

    #-------------------------------------------
    # Credentials from Environment
    #-------------------------------------------
    username = os.getenv('FB_USERNAME')
    password = os.getenv('FB_PASSWORD')

    #-------------------------------------------
    # Get Facebook User Token
    #-------------------------------------------
    now_start = datetime.now()
    print(now_start.strftime('%H:%M:%S'),
        'Obtaining Facebook User and Page tokens...')

    token = fb_token(username, password)

    if args.page_id == 'all':
        pages = list(token.id_to_page.keys())
    else:  # assuming comma-separated numeric Page IDs
        pages = args.page_id.split(',')

    now_end = datetime.now()
    now_mins = round((now_end - now_start).total_seconds() / 60, 1)
    print(now_end.strftime('%H:%M:%S'),
        f' -- Token Acquisition Time: {now_mins} minutes')

    #-------------------------------------------
    # Loop Over Facebook Pages
    #-------------------------------------------
    # Importantly, after data is pulled from each page, we push
    # the data to S3... This way, if a crash occurs, we have
    # data saved and technically only need to loop over the
    # remaining pages....
    now_start = datetime.now()
    print(now_start.strftime('%H:%M:%S'),
        'Begin Graph API Data Extraction...')
    for page_id in pages:
        page_name = token.id_to_page[page_id]
        now_this = datetime.now().strftime('%H:%M:%S')
        print(f'  {now_this}: Retrieving data for {page_id}:  {page_name}')

        # GET DATA FROM PAGE
        try:
            data = helper.get_video_insights_tables(
                token,
                page_id,
                since=args.since,  # defaults to 15 days ago
                add_date=True,
            )

            # WRITE EACH TABLE TO CSV, PUSH TO S3, THEN REMOVE CSV
            now_this = datetime.now().strftime('%H:%M:%S')
            print(f'    -- {now_this}: Pushing data to S3...')
            try:
                for table in data:
                    localfilename = f'{page_id}_{today}_{table}.csv'
                    localfilepath = current_directory + f'/{localfilename}'
                    data[table].to_csv(localfilename, index=False)
                    keypath = args.s3keypath + f'{page_id}/{today}/'
                    s3.csv_to_s3(
                        localfilepath,
                        args.s3bucket,
                        keypath,
                    )
                    os.remove(localfilename)
            except:
                print("ERROR: Issue pushing data to S3.")

        except:
            print("ERROR: Issue retrieving data from Facebook Graph.")

    now_end = datetime.now()
    now_mins = round((now_end - now_start).total_seconds() / 60, 1)
    print(now_end.strftime('%H:%M:%S'),
          f' -- Total Data Extraction Time: {now_mins} minutes')
