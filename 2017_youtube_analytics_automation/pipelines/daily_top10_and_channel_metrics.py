#!/home/ubuntu/anaconda/bin/python

from datetime import datetime, timedelta
from pandas import read_sql_query as qry

#======================================================
# Edge Cases
#======================================================
#
# [1] A video was public two days ago, private yesterday, and
# public again today.
#    In this case, YouTube might reinstantiate the cumulated
#    views today that it had from two days ago... However,
#    yesterday will coalesce to 0 in the SQL statement.  So,
#    in this case, you might notice a video suddenly have an
#    incredibly huge amount of daily views... This is artificial.
#    Not sure how to really avoid this situation w/o making the
#    code to messy and long...
#
# [2] A video is public today, but did not exist before today.
#    In this case, yesterday's views will coalesce to 0 in
#    the SQL statement, and the daily views will then be
#    dailyViews = todaysCumulative - 0 = todaysCumulative.
#
# [3] A video is not public today, but was public yesterday.
#    In this case, today's views will coalesce to 0 in the 
#    SQL statement, while yesterday's will be some positive
#    number.  This results in a negative number, which is
#    fine considering -- how else would you compute the
#    daily views.  This can be unfortunate if the video
#    was a high performer, but seriously: what can you do?
#    Your data table has a measurement from yesterday at 
#    3am and one from today at 3am.  Not much more you
#    can do!  You can't go back 12 hours and get an extra
#    measurement.

class YouTubeDaily:
    # EDIT: 2018-01-26: WHERE views >= 0
    #   The code does not account for some edge cases, one of
    #   them being that the digital team sometimes removes videos.
    #   When this happens, today's views COALESCE to 0, resulting
    #   in a negative daily difference.  If too many of these negatives
    #   occur, or even if a single, highly-viewed video is removed, then
    #   the negatives will outweigh the positives, and the channel sum
    #   will be negative... This doesn't look good in the emails that 
    #   go out!
    def __init__(self,
        con,
        channel_id,
        scrape_date,
        schema = 'analytics',
        source_table='youtube_daily_video_metrics',
        top10_table = 'youtube_daily_top10_video_metrics',
        channel_table = 'youtube_daily_channel_activity_metrics',
        testing = True,
    ):
        self.con = con
        self.source_table = f'{schema}.{source_table}'
        self.daily_top10_table = f'{schema}.{top10_table}'
        self.daily_channel_table = f'{schema}.{channel_table}'
        self.channel_id = channel_id
        self.scrape_date = scrape_date
        sd = datetime.strptime(scrape_date, '%Y-%m-%d')
        self.previous_day = (sd - timedelta(days=1)).strftime('%Y-%m-%d')
        self._ensure_valid_dates()
        self.testing = testing
        self._set_scrape_date_metric_column_defs()
        self._set_previous_day_metric_column_defs()
        self._set_top10_over_all_table_defs()
        self._set_top10_over_recent_table_defs()
        self._set_channel_overall_activity_table_defs()
        self._create_temp_table_for_daily_video_metrics()
        self._create_temp_table_for_recent_release_metrics()
    #-------------------------------------------
    # Ensure Both Dates Exist in Table
    #-------------------------------------------  
    def _ensure_valid_dates(self):
      date_table = qry(f"""
        SELECT scrapeDate
        FROM {self.daily_top10_table}
        GROUP BY scrapeDate
      """, self.con)
      table_dates = [date[0].strftime('%Y-%m-%d') for date in date_table.values]
      assert self.scrape_date in table_dates, \
          'scrapeDate not in tableDates'
      assert self.previous_day in table_dates, \
          'previousDay not in tableDates'
    #-------------------------------------------
    # Scrape Date Counts (Definitions)
    #-------------------------------------------  
    def _set_scrape_date_metric_column_defs(self):
        self.scrapeDatesComments = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.scrape_date}' 
              THEN comments END),0)
        """
        self.scrapeDatesDislikes = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.scrape_date}' 
              THEN dislikes END),0)
        """
        self.scrapeDatesLikes = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.scrape_date}' 
              THEN likes END),0)
        """
        self.scrapeDatesViews = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.scrape_date}' 
              THEN views END),0)
        """
    #-------------------------------------------
    # Previous Day Counts (Definitions)
    #-------------------------------------------  
    def _set_previous_day_metric_column_defs(self):
        self.previousDaysComments = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.previous_day}' 
              THEN comments END),0)
        """
        self.previousDaysDislikes = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.previous_day}' 
              THEN dislikes END),0)
        """
        self.previousDaysLikes = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.previous_day}' 
              THEN likes END),0)
        """
        self.previousDaysViews = f"""
            COALESCE(SUM(CASE 
              WHEN scrapedate='{self.previous_day}' 
              THEN views END),0)
        """
    #-------------------------------------------  
    # Metric Top10s Over All Videos 
    #-------------------------------------------  
    def _set_top10_over_all_table_defs(self): 
        self.top10CommentedOverAllVideos = """
          SELECT *,
            'comments' AS rankmetric,
            0 AS recentOnly
          FROM #metric_diffs_over_all_videos
          ORDER BY comments DESC
          LIMIT 10
        """
        self.top10DislikedOverAllVideos = """
          SELECT *,
            'dislikes' AS rankmetric,
            0 AS recentOnly
          FROM #metric_diffs_over_all_videos
          ORDER BY dislikes DESC
          LIMIT 10
        """
        self.top10LikedOverAllVideos = """
          SELECT *,
            'likes' AS rankmetric,
            0 AS recentOnly
          FROM #metric_diffs_over_all_videos
          ORDER BY likes DESC
          LIMIT 10
        """
        self.top10ViewedOverAllVideos = """
          SELECT *,
            'views' AS rankmetric,
            0 AS recentOnly
          FROM #metric_diffs_over_all_videos
          ORDER BY views DESC
          LIMIT 10
        """
    #-------------------------------------------  
    # Metric Top10s Over Recent Videos 
    #-------------------------------------------  
    def _set_top10_over_recent_table_defs(self): 
        self.top10CommentedOverRecentVideos = """
          SELECT *,
            'comments' as rankmetric,
            1 AS recentOnly
          FROM #metrics_over_recent_videos
          ORDER BY comments DESC
          LIMIT 10
        """
        self.top10DislikedOverRecentVideos = """
          SELECT *,
            'dislikes' as rankmetric,
            1 AS recentOnly
          FROM #metrics_over_recent_videos
          ORDER BY dislikes DESC
          LIMIT 10
        """
        self.top10LikedOverRecentVideos = """
          SELECT *,
            'likes' as rankmetric,
            1 AS recentOnly
          FROM #metrics_over_recent_videos
          ORDER BY likes DESC
          LIMIT 10
        """
        self.top10ViewedOverRecentVideos = """
          SELECT *,
            'views' as rankmetric,
            1 AS recentOnly
          FROM #metrics_over_recent_videos
          ORDER BY views DESC
          LIMIT 10
        """
    #-------------------------------------------  
    # Daily Channel-Level Metric Counts
    #-------------------------------------------  
    def _set_channel_overall_activity_table_defs(self):
        self.channelMetricsOverAllVideos = """
            SELECT channelId,
              channel,
              viewDate,
              SUM(comments) AS comments,
              SUM(dislikes) AS dislikes,
              SUM(likes) AS likes,
              SUM(views) AS views,
              0 AS recentOnly
            FROM #metric_diffs_over_all_videos
              WHERE views >= 0
            GROUP BY channelId, channel, viewDate
        """
        self.channelMetricsOverRecentVideos = """
            SELECT channelId,
              channel,
              viewDate,
              SUM(comments) AS comments,
              SUM(dislikes) AS dislikes,
              SUM(likes) AS likes,
              SUM(views) AS views,
              1 AS recentOnly
            FROM #metrics_over_recent_videos
              WHERE views >= 0
            GROUP BY channelId, channel, viewDate
        """
    #-------------------------------------------  
    # Metric Diffs Temp Tables (All, Recent)
    #-------------------------------------------  
    def _create_temp_table_for_daily_video_metrics(self):
        # Metric Diffs Over Any/All Videos 
        #   This table computes metrics for videos with any
        #   publishedAt date 
        self.con.execute(f"""
            DROP TABLE IF EXISTS #metric_diffs_over_all_videos;
            CREATE TABLE #metric_diffs_over_all_videos AS
              SELECT channelId,
                channel,
                videoId,
                MAX(title) AS title,
                '{self.previous_day}'::date AS viewDate,
                {self.scrapeDatesComments} - {self.previousDaysComments} AS comments,
                {self.scrapeDatesDislikes} - {self.previousDaysDislikes} AS dislikes,
                {self.scrapeDatesLikes} - {self.previousDaysLikes}       AS likes,
                {self.scrapeDatesViews} - {self.previousDaysViews}       AS views,
                MAX(publishedAt) AS publishedAt
              FROM {self.source_table}
                WHERE scrapeDate IN ('{self.scrape_date}', '{self.previous_day}')
                  AND channelId = '{self.channel_id}'
              GROUP BY 1,2,3
        """)
    def _create_temp_table_for_recent_release_metrics(self):
        # Metric Diffs Over Recent Videos 
        #   This table isolates the metric diffs for videos with a
        #   publishedAt date within past week.
        self.con.execute("""
            DROP TABLE IF EXISTS #metric_diffs_over_recent_videos;
            CREATE TABLE #metric_diffs_over_recent_videos AS
              SELECT * 
              FROM #metric_diffs_over_all_videos
                WHERE publishedAt + 7 > current_date;
        """)
    #-------------------------------------------  
    # Daily Top 10 
    #-------------------------------------------  
    def update_daily_top10_tables(self):
        # Is this a test, or the real thing?!
        if self.testing:
            print('Testing top 10...')
            print('\nTop 10 Viewed Over All Videos')
            print(qry(self.top10ViewedOverAllVideos, self.con))
            print('\nChannel Metrics Over All Videos')
            print(qry(self.channelMetricsOverAllVideos, self.con))
            print('\nTop 10 Viewed Over Recent Videos')
            print(qry(self.top10ViewedOverRecentVideos, self.con))
            print('\nChannel Metrics Over Recent Videos')
            print(qry(self.channelMetricsOverRecentVideos, self.con))
        else:
            print('Top 10: This is not a test!')
            # Lifetime Counts
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10CommentedOverAllVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10LikedOverAllVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10DislikedOverAllVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10ViewedOverAllVideos)
            # Recent Counts
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10CommentedOverRecentVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10LikedOverRecentVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10DislikedOverRecentVideos)
            self.con.execute(f"INSERT INTO {self.daily_top10_table} " +\
                    self.top10ViewedOverRecentVideos)
    #-------------------------------------------  
    # Daily Channel Activity
    #-------------------------------------------  
    def update_daily_channel_activity_tables(self):
        # Is this a test, or the real thing?!
        if self.testing:
            print('Testing channel activity...')
            print('\nChannel Metrics Over All Videos')
            print(qry(self.channelMetricsOverAllVideos, self.con))
            print('\nChannel Metrics Over Recent Videos')
            print(qry(self.channelMetricsOverRecentVideos, self.con))
        else:
            print('Channel Activity: This is not a test!')
            # Lifetime Counts
            self.con.execute(f"INSERT INTO {self.daily_channel_table} " +\
                    self.channelMetricsOverAllVideos)
            # Recent Counts
            self.con.execute(f"INSERT INTO {self.daily_channel_table} " +\
                    self.channelMetricsOverRecentVideos)