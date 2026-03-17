#!/home/ubuntu/anaconda/bin/python
import os
import sys
from dotenv import load_dotenv
import argparse
from datetime import datetime
import pytz


from youtube_analytics_automation.api import data_api
from youtube_analytics_automation.utils.registry import channel_name_to_id
from youtube_analytics_automation.utils.aws import (
    connect_to_redshift,
    csv_to_s3,
    s3_to_redshift,
)


#-------------------------------------------
# Environment Vars
#-------------------------------------------  
load_dotenv() 
USER         = os.getenv("REDSHIFT_USER")
PASSWORD     = os.getenv("REDSHIFT_PASSWORD")
HOST         = os.getenv("REDSHIFT_HOST")
DATABASE     = os.getenv("YOUTUBE_DATABASE")
PORT         = '5439'
IAM_ARN_ROLE = os.getenv('YOUTUBE_IAM_ROLE')


if __name__ == '__main__':
    #-------------------------------------------
    # Command Line Arguments
    #-------------------------------------------  
    parser = argparse.ArgumentParser()
    parser.add_argument("name", 
        choices = ['channel_01', 'channel_02', 'channel_03'],
        help="name of YouTube channel",
    )
    parser.add_argument("--testing", 
        action="store_true",
        help="Unset this flag to insert data into production table. "+\
             "Default: Data is inserted into a test table.",
    )
    parser.add_argument("--s3-bucket", 
        default="analytics_lake",
        help="Optional: Specify S3 bucket (defaults: 'analytics_lake')",
    )
    parser.add_argument("--s3-key", 
        default="youtube",
        help="Optional: Specify S3 keypath (defaults: 'youtube/<yyyymmdd>')",
    )
    parser.add_argument("--rs-schema", 
        default="analytics",
        help="Optional: Specify Redshift schema (defaults: 'analytics')",
    )
    parser.add_argument("--rs-table", 
        default="youtube_daily_video_metrics",
        help="Optional: Specify Redshift table (defaults: 'youtube_daily_video_metrics')",
    )
    parser.add_argument("--iam-arn-role", 
        default=None,
        help="Optional: If not used, it is expected you have setup a .env file."
    )

    #-------------------------------------------
    # Hello World
    #-------------------------------------------  
    args = parser.parse_args()
    channel_id = channel_name_to_id[args.name]
    print('YouTube Channel: '+args.name.upper())
    print('--------------------------------------')
    print('\nRunning youtube_daily_video_metrics.py...')

    #-------------------------------------------
    # Test Run or Deployment
    #-------------------------------------------  
    if args.testing:
        print("\nTesting...")
        rs_table = f"{args.rs_table}_teset"
    else:
        print("\nThis is NOT a test!")
        rs_table = args.rs_table

    #-------------------------------------------
    # YouTube Data API to DataFrame
    #-------------------------------------------  
    timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime('%H:%M:%S')
    print('\n', timestamp, "Pinging Data API for current metrics...")
    dapi = data_api.connect_to_data_api()
    data = data_api.get_channel_uploads_video_metrics(
            dapi, channel_id)


    #-------------------------------------------
    # DataFrame to CSV
    #-------------------------------------------  
    timestamp = datetime.now(pytz.timezone('EST')).strftime('%H:%M:%S')
    print('\n', timestamp, 'Saving data to CSV file on EC2...')
    localpath = sys.path[0] + '/'
    filename  = rs_table + \
        '_' + datetime.now().strftime('%Y%m%d') +\
        '_' + args.name+'.csv'
    localfile = localpath + filename
    data.to_csv(localfile, index=False)


    #-------------------------------------------
    # CSV to S3
    #-------------------------------------------  
    timestamp = datetime.now(pytz.timezone('EST')).strftime('%H:%M:%S')
    print('\n', timestamp, 'Pushing CSV file to S3...')
    csv_to_s3(localfile, args.s3_bucket, args.s3_key)


    #-------------------------------------------
    # S3 to Redshift
    #-------------------------------------------  
    iam_arn_role = args.iam_arn_role if args.iam_arn_role is not None else IAM_ARN_ROLE
    timestamp = datetime.now(pytz.timezone('EST')).strftime('%H:%M:%S')
    print('\n', timestamp, 'Transferring data from S3 to Redshift...')
    con = connect_to_redshift(USER, PASSWORD, HOST, DATABASE, port=PORT)
    s3_to_redshift(con, iam_arn_role, filename, args.s3_bucket, args.s3_key,
        args.rs_schema, rs_table)


    #-------------------------------------------
    # Delete File From EC2
    #-------------------------------------------  
    timestamp = datetime.now(pytz.timezone('EST')).strftime('%H:%M:%S')
    print('\n', timestamp, 'Success! Deleting file from EC2...')
    os.remove(localfile)
 