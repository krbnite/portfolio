#!/usr/bin/env python
"""
Written by Kevin Urban (2018)

Real-time multi-platform live event analytics pipeline. Collects audience
metrics from Facebook, YouTube, Twitter/Periscope, App (GA), DotCom (Conviva),
and Network (Conviva) during a live streaming event, and writes the aggregated
results into a Redshift reporting table.
"""
import argparse
import os
import re
import sys
from datetime import datetime
from random import choice

import pytz
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from platforms import facebook, youtube, twitter, app, dotcom, network
from utils import redshift

#--------------------------------------------------------
# NOTES: Try/Except
#--------------------------------------------------------
#   Each platform has (possibly nested) try/except statements
#     so that the failure of one platform's data collection does
#     not screw up data collection from all other platforms.
#
# * The end_time input is not mandatory, but is highly recommended.
#   If it is not listed, then the sentinel will pick up the end
#   time. However, if the live event is not on Facebook, then
#   this is problematic: no end_time will be listed to allow
#   the Network, App, and DotCom queries to be made... In this
#   case, it is probably best not to schedule on Cron and
#   just wait for the event to end, then run like so:
#
#      python run_live_report.py eventName brand date startTime endTime --no-facebook


if __name__ == '__main__':

    #===================================================================
    # Command Line Arguments
    #===================================================================
    parser = argparse.ArgumentParser()
    default_event_date = datetime.now(pytz.timezone('EST')).strftime('%Y-%m-%d')
    parser.add_argument(
        "event_name",
        help="Name of the live event.",
    )
    parser.add_argument(
        "brand",
        choices=['ppv', 'nxt', 'hof', 'specialty', 'now', 'other'],
        help="Type of event (ppv, nxt, hof, specialty, now, other).",
    )
    parser.add_argument(
        "event_date",
        help="Date of event (YYYY-MM-DD).",
    )
    parser.add_argument(
        "start_time",
        help="Start time of event (e.g., 19:00:00).",
    )
    parser.add_argument(
        "--end-time",
        default=None,
        help="End time of event (e.g., 19:59:59).",
    )
    parser.add_argument(
        "--table",
        default="content_kickoff_report_live",
        help="Base name of Redshift table (defaults to table_name_test).",
    )
    parser.add_argument(
        "--facebook-page-id",
        default=None,
        help="Page ID of the Facebook Page broadcasting the event.",
    )
    parser.add_argument(
        "--youtube-channel",
        default="",
        help="YouTube channel name (used for channel-selection if prompted).",
    )
    parser.add_argument(
        "--youtube-filter",
        default='kickoff',
        help="Word to filter YouTube's completed live event list.",
    )
    # Platform Skipping Arguments
    parser.add_argument(
        "--no-facebook",
        action="store_true",
        help="Set this to skip Facebook data collection. "
             "WARNING: This also skips the Facebook Sentinel, which can crash the "
             "program if there are network/app/dotcom queries and no end_time is "
             "specified.",
    )
    parser.add_argument(
        "--no-youtube",
        action="store_true",
        help="Set this to skip YouTube data collection.",
    )
    parser.add_argument(
        "--no-twitter",
        action="store_true",
        help="Set this to skip Twitter data collection.",
    )
    parser.add_argument(
        "--no-dotcom",
        action="store_true",
        help="Set this to skip DotCom data collection.",
    )
    parser.add_argument(
        "--no-app",
        action="store_true",
        help="Set this to skip App data collection.",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Set this to skip Network data collection.",
    )
    # Facebook Sentinel Arguments
    parser.add_argument(
        "--delay",
        default="600",
        help="Seconds to wait between end of live stream and data collection.",
    )
    parser.add_argument(
        "--no-sentinel",
        action="store_true",
        help="Turn off the sentinel.",
    )
    # Not a Test (Safety Feature)
    parser.add_argument(
        "--not-a-test",
        action="store_true",
        help="Set this flag to insert data into production table. "
             "Default: Data is inserted into a test table.",
    )
    args = parser.parse_args()
    event_dir = args.event_date + '__' + re.sub('[ ()#:?!_\\-\\.]', '', args.event_name)
    if not os.path.exists(event_dir):
        os.mkdir(event_dir)
    else:
        rand_num = str(choice(range(1000)))
        os.mkdir(event_dir + '__' + rand_num)

    if args.no_facebook:
        args.no_sentinel = True


    #===================================================================
    # Is this the real life, or is this just fantasy?
    #===================================================================
    if args.not_a_test:
        print(f'\nNot a test: Using {args.table}')
    else:
        args.table += '_test'
        print(f'\nThis is a test: Using {args.table}')


    #===================================================================
    # Connect to Redshift
    #===================================================================
    con_prod = redshift.connect(
        os.getenv('REDSHIFT_USER'),
        os.getenv('REDSHIFT_PASSWORD'),
        os.getenv('REDSHIFT_HOST'),
        os.getenv('REDSHIFT_DB'),
    )
    con_dev = redshift.connect(
        os.getenv('REDSHIFT_DEV_USER'),
        os.getenv('REDSHIFT_DEV_PASSWORD'),
        os.getenv('REDSHIFT_DEV_HOST'),
        os.getenv('REDSHIFT_DEV_DB'),
    )


    #===================================================================
    # Initialize Event's Row in Redshift Table
    #===================================================================
    # Note: We purposely do not initiate the table with end_time
    #   for live events which are open ended. The Facebook Sentinel
    #   outputs the recorded end time, and if the event's end time
    #   is not pre-specified in the command line args, then the FB
    #   time is used.
    print('\nInitializing new event row in Redshift table...')
    con_prod.execute(f"""
        INSERT INTO busgrp.{args.table} (
          event_name, event_date, start_time, brand
        ) VALUES ('{args.event_name}', '{args.event_date}',
          '{args.event_date} {args.start_time}', '{args.brand}');
    """)


    #===================================================================
    # Facebook
    #===================================================================
    if args.no_facebook:
        print('Skipping Facebook...')
        print('  ==> Skipping Facebook Sentinel')
        fb_end_time = None
    else:
        try:
            print('Getting Facebook user token...')
            fb_token = facebook.fb_token(
                    os.getenv('FB_USERNAME'),
                    os.getenv('FB_PASSWORD'))
            print('Exchanging user token for page token...')
            fb_token.change_token_by_id(args.facebook_page_id)

            try:
                fb_live_id, fb_video_id = facebook.get_video_ids(fb_token)
                with open(event_dir + '/facebook_id', 'w') as f:
                    f.write(str(fb_video_id))
            except:
                print('ERROR: No live video running...')

        except:
            print('ERROR: Facebook token...')

        #===================================================================
        # Begin Facebook Sentinel (monitor live stream)
        #===================================================================
        #  -- this sentinel observes live video node and monitors the
        #     live/vod status of the stream
        #  -- when the stream goes VOD, a 10-minute timer is set,
        #     the end of which marks the time we grab video insights
        #     data from the video ID node
        #  -- Facebook is the only time-sensitive data collection
        #     component of this pipeline; after collecting video insights,
        #     we move to collecting everything else
        if args.no_sentinel:
            print('Skipping the Sentinel...')
            fb_end_time = None
        else:
            try:
                fb_end_time = facebook.sentinel(
                    fb_token,
                    fb_live_id,
                    delay=args.delay,
                    hard_cutoff_time=f'{args.event_date} {args.end_time}'
                )
            except:
                print('ERROR: Facebook Sentinel failed.\n'
                        'No worries: Facebook ID saved in event directory.\n'
                        'NOTE: Collect other platform data by manually running '
                        'platform programs or restarting main script.')
                assert False, None


        #===================================================================
        # FB Data Collection
        #===================================================================
        #  -- to be consistent with prior reports, we collect the 3s views
        #     metric from video insights, which corresponds with the old
        #     "screen capture" method on the Page Insights GUI
        #  -- however, the plays/streams metric from the video insights edge
        #     is arguably more consistent with what YouTube reports for
        #     live playbacks/streams
        #  -- we wait ~10 minutes to access video insights to allow metrics
        #     to stabilize post-broadcast (per FB documentation)
        print('Working on Facebook...')
        try:
            facebook_data = facebook.get_video_insights(fb_token, fb_video_id)
            try:
                facebook.to_redshift(con_prod, args.table, args.event_name,
                        args.event_date, args.brand, facebook_data, fb_video_id)
            except:
                print('WARNING: Facebook data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving Facebook data; not inserted into Redshift.')


    #===================================================================
    # YouTube
    #===================================================================
    if args.no_youtube:
        print('Skipping YouTube...')
    else:
        print('Working on YouTube...')
        try:
            youtube.download_csv_file(
                event_dir,
                os.getenv('OKTA_USERNAME'),
                os.getenv('OKTA_PASSWORD'),
                channel=args.youtube_channel,
                filter_word=args.youtube_filter,
            )
            try:
                youtube_data = youtube.extract_data_from_csv(event_dir)
                youtube.to_redshift(con_prod, args.table, args.event_name, args.event_date,
                        args.brand, youtube_data)
            except:
                print('WARNING: YouTube data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving YouTube data; not inserted into Redshift.')


    #===================================================================
    # Twitter / Periscope
    #===================================================================
    #  -- the metric used here is the number of live viewers, which
    #     represents unique user accounts, and is therefore different
    #     than YT playbacks or FB 3s views
    if args.no_twitter:
        print('Skipping Twitter...')
    else:
        print('Working on Twitter...')
        try:
            twt_data = twitter.get_data(
                event_dir,
                os.getenv('TWITTER_USERNAME'),
                os.getenv('TWITTER_PASSWORD'),
            )
            twt_live_viewers = twitter.get_live_viewers(twt_data)
            try:
                twitter.to_redshift_live(
                    con_prod,
                    args.table,
                    args.event_name,
                    args.event_date,
                    args.brand,
                    twt_live_viewers,
                )
            except:
                print('WARNING: Twitter data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving Twitter data; not inserted into Redshift.')


    #===================================================================
    # End Time
    #===================================================================
    # -- the following platforms require end_time
    # -- for most events we know the end time ahead of the airing,
    #    however for open-ended live streams it is not known in advance,
    #    so end_time is not a mandatory input
    # -- to ensure there exists an end_time var, we monitored the live
    #    stream on Facebook above and recorded when the stream went VOD
    if (args.end_time is None) and (fb_end_time is None):
        print('Skipping DotCom, App, and Network: No end_time variable...')
    else:
        print('Inserting end_time into table...')
        if args.end_time is None:
            args.end_time = fb_end_time
        con_prod.execute(f"""
            UPDATE busgrp.{args.table}
            SET end_time='{args.event_date} {args.end_time}'
            WHERE event_name='{args.event_name}'
              AND event_date='{args.event_date}'
              AND brand='{args.brand}'
        """)


    #===================================================================
    # Dot Com
    #===================================================================
    if args.no_dotcom:
        print('Skipping DotCom...')
    else:
        print('Working on DotCom...')
        try:
            dotcom_plays = dotcom.get_live_global(
                con_prod, con_dev,
                args.event_date, args.start_time, args.end_time
            )
            dotcom_plays_us = dotcom.get_live_us(
                con_prod, con_dev,
                args.event_date, args.start_time, args.end_time
            )
            try:
                dotcom.to_redshift(
                    con_prod, args.table,
                    args.event_name, args.event_date, args.brand,
                    dotcom_plays, dotcom_plays_us,
                )
            except:
                print('WARNING: DotCom data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving DotCom data; not inserted into Redshift.')


    #===================================================================
    # App
    #===================================================================
    if args.no_app:
        print('Skipping App...')
    else:
        print('Working on App...')
        try:
            app_metric = app.app_numbers_live(
                con_prod,
                args.event_date,
                args.start_time,
                args.end_time,
            )
            try:
                app.to_redshift(
                    con_prod, args.table,
                    args.event_name, args.event_date, args.brand,
                    app_metric,
                )
            except:
                print('WARNING: App data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving App data; not inserted into Redshift.')


    #===================================================================
    # Network
    #===================================================================
    if args.no_network:
        print('Skipping Network...')
    else:
        print('Working on Network...')
        try:
            max_concurrents = network.get_live_global(
                con_prod, con_dev,
                args.event_date, args.start_time, args.end_time,
            )
            max_concurrents_us = network.get_live_us(
                con_prod, con_dev,
                args.event_date, args.start_time, args.end_time,
            )
            try:
                network.to_redshift(
                    con_prod, args.table,
                    args.event_name, args.event_date, args.brand,
                    max_concurrents, max_concurrents_us,
                )
            except:
                print('WARNING: Network data not inserted into Redshift table.')
        except:
            print('WARNING: Issue retrieving Network data; not inserted into Redshift.')
