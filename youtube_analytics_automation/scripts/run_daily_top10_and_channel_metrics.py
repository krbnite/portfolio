import os
from dotenv import load_dotenv
import argparse
import pytz
from datetime import datetime

from youtube_analytics_automation.utils.aws import connect_to_redshift
from youtube_analytics_automation.pipelines.daily_top10_and_channel_metrics import YouTubeDaily

#-------------------------------------------
# Redshift Credentials
#-------------------------------------------  
load_dotenv() 
USER = os.getenv("REDSHIFT_USER")
PASSWORD = os.getenv("REDSHIFT_PASSWORD")
HOST = os.getenv("REDSHIFT_HOST")
DATABASE = os.getenv("YOUTUBE_DATABASE")
PORT = '5439'

#-------------------------------------------
# Redshift Connection
#-------------------------------------------  
con = connect_to_redshift(USER, PASSWORD, HOST, DATABASE, port=PORT)


channel_name_to_id = {
    'channel_01': 'channel_id_01', 
    'channel_02': 'channel_id_02', 
    'channel_03': 'channel_id_03'
}

#-------------------------------------------
# Main
#-------------------------------------------  
if __name__ == '__main__':
    print('\n\nRunning youtube_daily_top10_and_channel_metrics.py\n')
    #-------------------------------------------
    # Command Line Arguments
    #-------------------------------------------  
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', 
        choices = ['channel_01', 'channel_02', 'channel_03'],
        help = 'Name of YouTube channel.',
    )
    parser.add_argument(
        '--scrape-date', 
        default = datetime.now(pytz.timezone('EST')).strftime('%Y-%m-%d'),
        help = 'Date metrics were scraped from Data API. '+\
                'Note that viewDate = scrapeDate-1.',
    )
    parser.add_argument(
        '--testing',
        action='store_true',
        help = 'Turn this flag off to insert data into production table (default: true).',
    )
    parser.add_argument(
        '--schema',
        default = 'analytics',
        help = 'Defaults to "analytics"',
    )
    parser.add_argument(
        '--top10-table',
        default = 'youtube_daily_top10_video_metrics',
        help = 'Defaults to youtube_daily_top10_video_metrics',
    )
    parser.add_argument(
        '--channel-table',
        default = 'youtube_daily_channel_activity_metrics',
        help = 'Defaults to youtube_daily_channel_activity_metrics',
    )
    args = parser.parse_args()

    #-------------------------------------------
    # Chosen Parameters
    #-------------------------------------------  
    channel_id = channel_name_to_id[args.name]
    youtube = YouTubeDaily(con, 
        channel_id, args.scrape_date, schema = args.schema, 
        top10_table=args.top10_table, channel_table=args.channel_table, 
        testing=args.testing,
    )
    youtube.update_daily_top10_tables()
    youtube.update_daily_channel_activity_tables()


