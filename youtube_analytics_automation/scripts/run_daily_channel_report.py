#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders

import pytz
from pandas import read_sql_query as qry
from dotenv import load_dotenv

from youtube_analytics_automation.utils import redshift
from youtube_analytics_automation.utils.registry import channel_name_to_id

load_dotenv()

channel_proper_name = {
    'channel_01': 'Channel 01',
    'channel_02': 'Channel 02',
    'channel_03': 'Channel 03',
}

if __name__ == '__main__':
    today = datetime.now(pytz.timezone('EST'))
    yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name',
        choices=['channel_01', 'channel_02', 'channel_03'],
        help='Name of YouTube channel',
    )
    parser.add_argument(
        '--viewdate',
        default=yesterday,
        help='YYYY-MM-DD',
    )
    parser.add_argument(
        '--not-a-test',
        action='store_true',
        help='Set this flag to send to the distribution list. Default: send only to sender.',
    )
    args = parser.parse_args()
    channel_id   = channel_name_to_id[args.name]
    channel_name = channel_proper_name[args.name]

    #-------------------------------------------
    # Credentials
    #-------------------------------------------
    SENDER   = os.getenv('EMAIL_SENDER')
    EMAIL_PW = os.getenv('EMAIL_PASSWORD')

    #-------------------------------------------
    # Connect to Redshift
    #-------------------------------------------
    con = redshift.connect(
        os.getenv('REDSHIFT_USER'),
        os.getenv('REDSHIFT_PASSWORD'),
        os.getenv('REDSHIFT_HOST'),
        os.getenv('YOUTUBE_DATABASE'),
        port='5439',
    )
    ex = con.execute

    #-------------------------------------------
    # Top 10 (Recent and All-Time)
    #-------------------------------------------
    top10 = qry(f"""
        SELECT *
        FROM analytics.youtube_daily_top10_video_metrics
          WHERE viewDate='{args.viewdate}'
            AND channelId='{channel_id}'
    """, con)

    #-------------------------------------------
    # CMR: Channel Metrics (Recent)
    #   -- "Recent" = videos published in past 7 days
    #   -- Days 0-3: pulled from the incremental metrics table
    #   -- Days 4-30: pulled from the reporting API detail table, which lags
    #      a few days but carries longer history
    #-------------------------------------------
    ex(f"""
      DROP TABLE IF EXISTS #cmr_00_03;
      CREATE TABLE #cmr_00_03 AS (
        SELECT channel,
          viewDate,
          dislikes,
          likes,
          views
        FROM analytics.youtube_daily_channel_activity_metrics
          WHERE viewDate IN (
              '{args.viewdate}',
              '{args.viewdate}'-1,
              '{args.viewdate}'-2,
              '{args.viewdate}'-3)
            AND channelId='{channel_id}'
            AND recentOnly=1
      );
    """)
    ex(f"""
      DROP TABLE IF EXISTS #cmr_04_30;
      CREATE TABLE #cmr_04_30 AS (
        SELECT channel,
          view_date::date AS viewDate,
          SUM(dislikes) AS dislikes,
          SUM(likes) AS likes,
          SUM(views) AS views
        FROM analytics.youtube_reporting_api_video_detail
          WHERE view_date::date BETWEEN '{args.viewdate}'-30 AND '{args.viewdate}'-4
            AND channelId='{channel_id}'
            AND debut_date + 7 > view_date::date
        GROUP BY view_date::date, channel
      );
    """)
    cmr = qry("""
        SELECT *
        FROM (
          (SELECT * FROM #cmr_00_03)
          UNION
          (SELECT * FROM #cmr_04_30)
        ) ORDER BY viewdate DESC;
    """, con)

    #-------------------------------------------
    # CMA: Channel Metrics (All-Time)
    #-------------------------------------------
    ex(f"""
      DROP TABLE IF EXISTS #cma_00_03;
      CREATE TABLE #cma_00_03 AS (
        SELECT channel,
          viewDate,
          dislikes,
          likes,
          views
        FROM analytics.youtube_daily_channel_activity_metrics
          WHERE viewDate IN (
              '{args.viewdate}',
              '{args.viewdate}'-1,
              '{args.viewdate}'-2,
              '{args.viewdate}'-3)
            AND channelId='{channel_id}'
            AND recentOnly=0
      );
    """)
    ex(f"""
      DROP TABLE IF EXISTS #cma_04_30;
      CREATE TABLE #cma_04_30 AS (
        SELECT channel,
          view_date::date AS viewDate,
          SUM(dislikes) AS dislikes,
          SUM(likes) AS likes,
          SUM(views) AS views
        FROM analytics.youtube_reporting_api_video_detail
          WHERE view_date::date BETWEEN '{args.viewdate}'-30 AND '{args.viewdate}'-4
            AND channelId='{channel_id}'
        GROUP BY view_date::date, channel
      );
    """)
    cma = qry("""
        SELECT *
        FROM (
          (SELECT * FROM #cma_00_03)
          UNION
          (SELECT * FROM #cma_04_30)
        ) ORDER BY viewdate DESC;
    """, con)

    #-------------------------------------------
    # Derived Quantities
    #-------------------------------------------
    # All Time
    top10_all = top10[
        (top10.rankmetric == 'views') & (top10.recentonly == 0)].\
        sort_values('views', ascending=False).\
        filter(items=['title', 'videoid', 'publishedat', 'views']).\
        reset_index(drop=True)
    top10_all.publishedat = [dt.strftime('%b %d, %Y') for dt in top10_all.publishedat]
    top10_all.columns = ['Title', 'Video ID', 'Date Published', 'Daily Views']

    cva0          = int(cma.views[0])
    cva7_day_avg  = cma.views[1:8].mean()
    cva30_day_avg = cma.views[1:].mean()
    cva_vs_7_day  = int(round(100 * (cva0 - cva7_day_avg)  / cva7_day_avg))
    cva_vs_30_day = int(round(100 * (cva0 - cva30_day_avg) / cva30_day_avg))

    # Recent
    top10_rec = top10[
        (top10.rankmetric == 'views') & (top10.recentonly == 1)].\
        sort_values('views', ascending=False).\
        filter(items=['title', 'videoid', 'publishedat', 'views']).\
        reset_index(drop=True)
    top10_rec.publishedat = [dt.strftime('%b %d, %Y') for dt in top10_rec.publishedat]
    top10_rec.columns = ['Title', 'Video ID', 'Date Published', 'Daily Views']

    cvr0          = int(cmr.views[0])
    cvr7_day_avg  = cmr.views[1:8].mean()
    cvr30_day_avg = cmr.views[1:].mean()
    cvr_vs_7_day  = int(round(100 * (cvr0 - cvr7_day_avg)  / cvr7_day_avg))
    cvr_vs_30_day = int(round(100 * (cvr0 - cvr30_day_avg) / cvr30_day_avg))

    #-------------------------------------------
    # Generate HTML Report from Template
    #-------------------------------------------
    styles = [
        dict(selector='th:first-child', props=[('display', 'none')]),
        dict(selector='tr:hover',       props=[('background-color', 'yellow')]),
    ]
    top10_all_html = top10_all.style.\
        set_table_styles(styles).\
        format('{:,}'.format, subset=['Daily Views']).\
        bar().\
        render()

    if len(top10_rec) != 0:
        top10_rec_html = top10_rec.style.\
            set_table_styles(styles).\
            format('{:,}'.format, subset=['Daily Views']).\
            bar().\
            render()
    else:
        # Channel published no content in the past 7 days.
        top10_rec_html = 'No Content Published in Past 7 Days.'
        cvr0 = 0

    template_path = os.path.join(sys.path[0], 'templates', 'channel_report.html')
    with open(template_path, 'r') as f:
        prehtml = f.read()
    html = prehtml.format(
        name      = channel_name,
        data_date = args.viewdate,
        alltime0  = '{:,}'.format(cva0),
        alltime1  = cva_vs_7_day,
        alltime2  = cva_vs_30_day,
        table1    = top10_all_html,
        recent0   = '{:,}'.format(cvr0),
        recent1   = cvr_vs_7_day,
        recent2   = cvr_vs_30_day,
        table2    = top10_rec_html,
    )

    report_dir = os.path.join(sys.path[0], 'most_recent_reports')
    os.makedirs(report_dir, exist_ok=True)
    report_filename = '-'.join(channel_name.split()) + '-on-YouTube__Yesterdays-Recap.html'
    report_path = os.path.join(report_dir, report_filename)
    with open(report_path, 'w') as f:
        f.write(html)

    #-------------------------------------------
    # Build Email
    #-------------------------------------------
    msg = MIMEMultipart()
    msg['Subject'] = f'{channel_name} on YouTube: Daily Channel Update'
    msg['From'] = SENDER

    if args.not_a_test:
        recipients = [
            'analyst_01@example.com',
            'analyst_02@example.com',
            'stakeholder_01@example.com',
        ]
    else:
        recipients = [SENDER]
    msg['To'] = ', '.join(recipients)

    msg.attach(MIMEText(f"""
        <html>
        <head></head>
        <body width="device-width">
        <table align="center" cellpadding="0" cellspacing="0">
          <tr><td>
            <table align="center" cellpadding="0" cellspacing="0">
              <tr><td><img src="cid:channel"></td></tr>
            </table>
            <table align="center" cellpadding="0" cellspacing="0">
              <tr><td><img src="cid:youtube"></td></tr>
            </table>
            <br>
            <table align="center" cellpadding="0" cellspacing="0">
              <tr><td>
                Please see the attached document for a daily update of
                yesterday's views for {channel_name} on YouTube.
              </td></tr>
            </table>
          </td></tr>
        </body>
        </html>
    """, 'html'))

    #-------------------------------------------
    # Inline Images
    #   -- Place channel logo as channel.jpg and the YouTube logo as
    #      youtube.png in a scripts/images/ directory.
    #-------------------------------------------
    images_dir = os.path.join(sys.path[0], 'images')
    with open(os.path.join(images_dir, 'channel.jpg'), 'rb') as fp:
        ch_img = MIMEImage(fp.read())
    with open(os.path.join(images_dir, 'youtube.png'), 'rb') as fp:
        yt_img = MIMEImage(fp.read())
    yt_img.add_header('Content-Id', '<youtube>')
    msg.attach(yt_img)
    ch_img.add_header('Content-Id', '<channel>')
    msg.attach(ch_img)

    #-------------------------------------------
    # Attach HTML Report
    #-------------------------------------------
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(report_path, 'rb').read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
        f'attachment; filename="{os.path.basename(report_path)}"')
    msg.attach(part)

    #-------------------------------------------
    # Send
    #-------------------------------------------
    domain = SENDER.split('@')[1]
    server = smtplib.SMTP(f'smtp.{domain}', 587)
    server.starttls()
    server.login(SENDER, EMAIL_PW)
    server.sendmail(SENDER, recipients, msg.as_string())
    server.close()
