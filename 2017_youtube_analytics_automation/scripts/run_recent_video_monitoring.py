#!/home/ubuntu/anaconda/bin/python
import os
from dotenv import load_dotenv
import argparse
import pandas as pd

from youtube_analytics_automation.utils import redshift 
from youtube_analytics_automation.api import data_api 
# from youtube_analytics_automation.utils.email import simple_email

load_dotenv() 

#-------------------------------------------
# Redshift Connection
#-------------------------------------------
USER = os.getenv('REDSHIFT_USER')
PASSWORD = os.getenv('REDSHIFT_PASSWORD')
HOST = os.getenv('REDSHIFT_HOST')
DATABASE = os.getenv('YOUTUBE_DATABASE')
PORT = '5439'
con = redshift.connect(USER, PASSWORD, HOST, DATABASE, port=PORT)
# Redshift Target
CONTENT_OWNER_ID = os.getenv('CONTENT_OWNER_ID')
SCHEMA='analytics'
TABLE='youtube_recent_video'

#-------------------------------------------
# Main
#-------------------------------------------
if __name__ == '__main__':
    #-------------------------------------------
    # Command Line Arguments
    #-------------------------------------------  
    parser = argparse.ArgumentParser()
    parser.add_argument("--testing", action="store_true",
        help="Unset this flag to insert data into production table. "+\
             "Default: Data is printed to screen."
    )
    args = parser.parse_args()

    #-------------------------------------------
    # YouTube DataAPI Connection
    #-------------------------------------------
    dapi = data_api.connect_to_data_api()

    #-------------------------------------------
    # Get YouTube Channels
    #-------------------------------------------
    name_to_id = data_api.get_channel_name_id_map(dapi, CONTENT_OWNER_ID)
    
    #-------------------------------------------
    # YouTube "Scrape"
    #-------------------------------------------
    #-----------------------------------------------------------
    # NOTE: It just so happens that in my particular use case,
    #    the time it took the different channels to get uploads
    #    was approximately in alphabetical order (i.e., "A" short,
    #    "Z" long), so I took advantage of this in order to get 
    #    as many scrapes as possible close to the hour mark 
    #-----------------------------------------------------------
    alphabetic_names = list(name_to_id.keys())
    alphabetic_names.sort()
    scrapes = pd.DataFrame(columns=['video_id', 'title', 'views', 'likes', 
        'dislikes', 'time_scraped_est', 'time_uploaded_est'])
    for name in alphabetic_names:
        print('Working on '+name+'...')
        # 1. Get channel uploads
        video_info = data_api.\
                get_channel_uploads_video_metrics(dapi, name_to_id[name])
        # 2. Filter out recent uploads
        latest = data_api.discard_content_older_than_7days(video_info)
        #-----------------------------------------------------------
        # NOTE FROM FUTURE: df.append is technically deprecated
        # -- it wasn't a great way to do this anyway because it
        #    could slow things down quite a bit
        # -- growing lists in a loop than converting to a DataFrame
        #    is the better way to go
        #-----------------------------------------------------------
        scrapes = scrapes.append(latest, ignore_index=True)
    
    #-------------------------------------------
    # Redshift Insertion
    #-------------------------------------------
    #  -- Issue #1: chunksize was added to hedge against queries getting
    #     booted between 530-730am when a bunch of ETL is going on
    #  -- Issue #2: Usually get booted from Redshift around 530am, and also 
    #     during cluster resizing episodes (usually occurs on weekends);
    #     try/except is added to hedge against program crash
    if args.testing:
        print('This is only a test...')
        print('Updating Redshift...')
        _ = redshift.update(scrapes, con, SCHEMA, TABLE, chunksize=150, not_a_test=False)
    else:
        print('Not a test!')
        print('Updating Redshift...')
        _ = redshift.update(scrapes, con, SCHEMA, TABLE, chunksize=150, not_a_test=True)