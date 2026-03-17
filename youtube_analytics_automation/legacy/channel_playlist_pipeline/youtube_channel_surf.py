import time
from datetime import datetime, timedelta
import re
import bs4
from selenium import webdriver
import pandas as pd
from pandas import read_sql_query as qry

#------------------------------------------------------------------------
class YouTubeChannelScraper():
    #--------------------------------------------------------------------
    def __init__(self,
            channel_id,
            con,
            visual=True,
            driver_path='/usr/local/share/chromedriver',
            new_only=True
            ):
        """
        Opens selenium browser. If visual is set to False,
        headless Chrome is employed (default: Chrome).
        """
        self.channel_id  = channel_id
        self.con         = con
        self.visual      = visual
        self.driver_path = driver_path
        self.new_only    =  new_only
        self.get_channel_name()
        self.playlists   = None
        self.cpv_scrape = None
        self.daily_video_views = None
        self.dvv_appended = False
        self.as_on_date = None

    #--------------------------------------------------------------------
    def get_channel_name(self):
        """
        """
        # Start Browser Service
        service = webdriver.chrome.service.Service(self.driver_path)
        service.start()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options = options.to_capabilities()
        driver = webdriver.Remote(service.service_url, options)
        driver.implicitly_wait(10)

        # Go to Channel Page
        youtube = 'https://www.youtube.com'
        channel_url = youtube+'/channel/'+self.channel_id+'/playlists'
        driver.get(channel_url)
        driver.implicitly_wait(3)
        page = bs4.BeautifulSoup(driver.page_source,'lxml')
        # Extract Data 
        channel_name = page.title.text.split(' - YouTube')[0].strip()
        self.channel_name = channel_name

    #--------------------------------------------------------------------
    def get_channel_playlists(self, new_only=None, visual=None):
        """
        Get up-to-date list of a channel's playlists given the channel ID.
        By default, only recently modified playlists are extracted. By
        setting new_only=False, the scraper will extract all playlists.
        """
        new_only = self.new_only if new_only is None else new_only
        visual = self.visual if visual is None else visual

        # Start Browser Service
        service = webdriver.chrome.service.Service(self.driver_path)
        service.start()
        if visual == True:
            options = {}
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options = options.to_capabilities()
        driver = webdriver.Remote(service.service_url, options)
        driver.implicitly_wait(10)

        # Go to Channel Page
        youtube = 'https://www.youtube.com'
        channel_url = youtube+'/channel/'+self.channel_id+'/playlists'
        driver.get(channel_url)
        driver.implicitly_wait(3)
        page = bs4.BeautifulSoup(driver.page_source,'lxml')
        # Extract Data
        list_name = [' '.join(item.text.split())
                for item in page.select('a[class="style-scope ytd-grid-playlist-renderer"]')]
        list_id = [item.attrs['href'].split('list=')[1]
                for item in page.select('a[class="style-scope ytd-grid-playlist-renderer"]')]
        list_url = [youtube + '/playlist?list='+item for item in list_id]
        list_update = [1 if num=='today' else 2 if num=='yesterday' else int(num)
                for num in [item.text.split(' ')[1] if item.text!= '' else '-1'
                    for item in page.select('span[class="style-scope ytd-video-meta-block"]')]]
        playlists = pd.DataFrame(columns=[
            'list_name','list_id','list_url',
            'channel_name','channel_id','channel_url'])
        for idx,is_new in enumerate(list_update):
            if new_only:
                if (is_new > 0):
                    playlists.loc[idx] = [list_name[idx], list_id[idx], list_url[idx],
                            self.channel_name, self.channel_id, channel_url]
            else: # Record All
                playlists.loc[idx] = [list_name[idx], list_id[idx], list_url[idx],
                    self.channel_name, self.channel_id, channel_url]
        driver.close()
        return playlists

    #--------------------------------------------------------------------
    def get_playlist_videos(self, list_id, list_name, new_only=None, visual=None):
        """
        """
        print("\tPlaylist:",list_name)
        new_only = self.new_only if new_only is None else new_only
        visual = self.visual if visual is None else visual
        #--------------------------
        # Start Browser Service
        #--------------------------
        service = webdriver.chrome.service.Service(self.driver_path)
        service.start()
        if visual == True:
            options = {}
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options = options.to_capabilities()
        driver = webdriver.Remote(service.service_url, options)
        driver.implicitly_wait(10)
        #--------------------------
        # Go to Playlist Page
        #--------------------------
        youtube = 'https://www.youtube.com'
        list_url = youtube+'/playlist?list='+str(list_id)
        driver.get(list_url)
        driver.implicitly_wait(3)
        there_is_more_to_load = True
        while there_is_more_to_load:
            try:
                load_more = driver.find_element_by_class_name("load-more-text")
                driver.implicitly_wait(10)
                load_more.click()
                #time.sleep(1)
                driver.implicitly_wait(10)
            except:
                there_is_more_to_load=False
        # WARNING: sometimes page loads w/o load more button and refresh is based on scrolling
        #--------------------------
        # Get Source Code
        #--------------------------
        page = bs4.BeautifulSoup(driver.page_source,'lxml')

        # Extract video info
        playlist = pd.DataFrame(columns=['video_name','video_id','video_url', 'views'])
        vlist = page.select('a[class="style-scope ytd-playlist-video-renderer"]')
        for idx,video in enumerate(vlist):
            info1 = video.select('span[id="video-title"]')[0]
            if 'aria-label' in info1.attrs.keys():
                info2 = info1.attrs['aria-label'].split(info1.attrs['title'])[1].split(self.channel_name)[-1]
                video_name = info1.attrs['title']
                video_id = video.a.attrs['href'].split('/watch?v=')[1].split('&')[0]
                video_url = youtube+video.a.attrs['href'].split('&list')[0]
                try:
                    time_since_release = info2.split()[0:2]  # e.g., ['2', 'days']
                except:
                    start_here = re.search('[0-9]',info2).start()
                    info2 = info1[start_here:]
                    time_since_release = info2.split()[0:2]  # e.g., ['2', 'days']
                num_views = int(''.join(info2.split()[-2].split(',')))
                if new_only:
                    if time_since_release[1] in ['seconds','minutes','hours','days']:
                        playlist.loc[idx] = [video_name, video_id, video_url, num_views]
                else:
                    playlist.loc[idx] = [video_name, video_id, video_url, num_views]
            else:
                if info1.attrs['title']=='[Private video]':
                    print('\t\t\t...private video encountered: no data.')
        driver.close()
        return playlist

    #--------------------------------------------------------------------
    def get_cpv_scrape(self):
        """
        Formerly coalesce_all_info (if) and construct_tables (else).
        """
        print("Channel:", self.channel_name)
        self.playlists = self.get_channel_playlists(self.channel_id)
        playlists = self.playlists
        columns = ['video_name','video_id','video_url', 'views'] + playlists.columns.tolist()
        cpv_scrape = pd.DataFrame(columns=columns)
        idx=0
        for i,playlist in playlists.iterrows():
            videos = self.get_playlist_videos(playlist['list_id'], playlist['list_name'])
            for j,video in videos.iterrows():
                cpv_scrape.loc[idx] = video.tolist() + playlist.tolist()
                idx+=1
        return cpv_scrape



    #--------------------------------------------------------------------
    # Added 2017-10-10.  
    # Note: Instead of going through a playlist, we go through all the
    #   videos listed at youtube.com/channel/channel_id/videos
    def get_daily_video_views(self, scroll_lim=1000000, sleep_time=1,
            visual=None):
        """
        scroll_lim: set to 1e6 by default, which is essentially infinite. Point is,
          that it should continue scrolling until page is done dynamically 
          generating.
        """

        visual = self.visual if visual is None else visual
        channel_id = self.channel_id

        #--------------------------
        # Start Browser Service
        #--------------------------
        service = webdriver.chrome.service.Service(self.driver_path)
        service.start()
        if visual:
            options = {}
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options = options.to_capabilities()
        driver = webdriver.Remote(service.service_url, options)
        driver.implicitly_wait(30); time.sleep(2)

        #--------------------------
        # Go to Channel's Videos Page
        #--------------------------
        youtube = 'https://www.youtube.com'
        url = youtube+'/channel/'+str(channel_id)+'/videos?flow=list'
        driver.get(url); time.sleep(2)
        #driver.implicitly_wait(30)#; 
        there_is_more_to_load = True
        old_height = driver.find_element_by_css_selector('ytd-browse').size['height']
        time.sleep(sleep_time)
        counter=0
        while there_is_more_to_load:
            driver.execute_script("window.scrollBy(0,10000)","")
            time.sleep(sleep_time)
            new_height = driver.find_element_by_css_selector('ytd-browse').size['height']
            time.sleep(sleep_time)
            counter+=1
            if (counter > scroll_lim):
                there_is_more_to_load = False
            if new_height == old_height:
                # Check one more time
                time.sleep(sleep_time+1)
                new_height = driver.find_element_by_css_selector('ytd-browse').size['height']
                time.sleep(sleep_time+1)
                if new_height == old_height:
                    there_is_more_to_load = False
            else:
                old_height = new_height
        #--------------------------
        # Get Source Code
        #--------------------------
        page = bs4.BeautifulSoup(driver.page_source,'lxml')

        # Get Timestamp Info
        timestamp = time.localtime()
        as_on_date = str(timestamp.tm_year)+'-'+str(timestamp.tm_mon)+'-'+str(timestamp.tm_mday)

        # Extract Video Info
        vidlist = pd.DataFrame(columns=[
            'channel_id', 'video_id', 'video_name', 'views', 'as_on_date', 
            'days_since_release', 'dsr_num', 'dsr_unit'])
        vlist = page.select('a[class="yt-simple-endpoint style-scope ytd-video-renderer"]')
        for idx,video in enumerate(vlist):
            if 'aria-label' in video.attrs.keys():
                video_name = video.attrs['title']
                video_id = video.attrs['href'].split('/watch?v=')[1].split('&')[0]
                #video_url = youtube+video.attrs['href'].split('&list')[0]
                temp = video.attrs['aria-label'].split(video_name)[1]
                info = temp.split(self.channel_name)[-1]
                # Days Since Release
                try:
                    days_since_release = info.split()[0:2]  # e.g., ['2', 'days']
                except:
                    start_here = re.search('[0-9]', info).start()
                    info2 = info2[start_here:]
                    days_since_release = info.split()[0:2]  # e.g., ['2', 'days']
                dsr_num = days_since_release[0]
                dsr_units = days_since_release[1]
                if dsr_units[0:3]=='min':
                    dsr = float(dsr_num) /(60*24)
                elif dsr_units[0:3]=='hou':
                    dsr = float(dsr_num)/ 24
                elif dsr_units[0:3]=='day':
                    dsr = float(dsr_num)
                elif dsr_units[0:3]=='wee':
                    dsr = float(dsr_num) * 7 # (x week) (7 day / week)
                elif dsr_units[0:3]=='mon':
                    dsr = float(dsr_num) * 30.4 # (x month)(30.4 day / month)
                elif dsr_units[0:3]=='yea':
                    dsr = float(dsr_num) * 365.25
                # Scrape Views
                num_views = int(''.join(info.split()[-2].split(',')))
                vidlist.loc[idx] = [
                        channel_id, video_id, video_name, num_views,
                        as_on_date, dsr, dsr_num, dsr_units]
            else:
                if info1.attrs['title']=='[Private video]':
                    print('\t\t\t...private video encountered: no data.')
        driver.close()
        self.as_on_date = vidlist.as_on_date[0]
        self.daily_video_views = vidlist



    #---------------------------------------------------------------------
    #channel_id = 'UCIJnHb6meZoOjKF68h35QgQ'
    # By def, we will never be updating the channels table this way...
    # To get new tables, one has to manually update the channels table.
    def redshift_append(self, tbl, tblnm):
        tbl.to_sql(tblnm, con=self.con, schema='your_schema',
                index=False, if_exists='append', chunksize=150)


    #def daily_video_views(self, scrape_data):
    #    return scrape_data.drop_duplicates()
    def append_daily_video_views(self,
            test=True,
            force=False,
            chunksize=1500):
        """
        The corresponding table in Redshift should only be updated once per
        day during the scheduled job.  However, often we need to experiment with
        the code, and such a constraint is highly restrictive.  To meet both
        needs, I have two flags, test and force:

        test: by default (test=True), the function assumes you are testing and will not
            write to your_schema.daily_video_views. In production, this
            parameter must be negated (test=False).
        force: As a further safety measure, if the as_on_date column in Redshift
            already has the current date, then the new data will not be written
            to Redshift.  By setting force=True, the old data in Redshift will
            be deleted and the new data will be inserted.
        tbl: daily_video_views_test can be used for code testing
            and debugging,. This variable is set to the main Redshift table, but
            can be changed to the test table (or any other one).
        """
        if test == True:
            print("\nTesting.. \nTo turn off test mode, set test=False.\n")
            tbl = 'daily_video_views_test'
        else:
            print("This is not a test!")
            tbl = 'daily_video_views'

        # scraped as_on_date is a string date
        #  -- must coerce queried dates into string dates
        scrape_data = self.daily_video_views
        as_on_date = self.as_on_date  #scrape_data.as_on_date[0] 
        dates = qry("""
            SELECT as_on_date
            FROM your_schema."""+tbl+"""
              WHERE channel_id='"""+self.channel_id+"""'
            GROUP BY as_on_date
            """, self.con).as_on_date.astype(str)
        if force == True:
            # Remove corresponding as_on_date from Redshift
            if as_on_date in dates.tolist():
                print("The as_on_date "+str(as_on_date)+" already in Redshift table.")
                print("\t\tDeleting...")
                self.con.execute("""
                    DELETE FROM your_schema."""+tbl+"""
                    WHERE as_on_date="""+as_on_date)
            else:
                print("Force was unnecessary this time...")
            # Insert new as_on_date data into Redshift
            print("Inserting new data...")
            self.redshift_append(scrape_data, tbl)
            self.dvv_appended=True
        else:
            # Only insert as_on_date data if as_on_date not in Redshift table
            if as_on_date not in dates.tolist():
                print("Updating Redshift table with new as_on_date...")
                self.redshift_append(scrape_data, tbl)
                self.dvv_appended=True
            else:
                print("The as_on_date "+str(as_on_date)+" already in Redshift table.")
                print("Did you want to force? (force=True)")


    def append_dvv_derivatives(self,
        as_on_date=None,
        test=True,
        force=False
    ):
        # Ensure data exists to run this fcn
        ## NOT SURE THIS PART IS REALLY NECESSARY.................
        #assert self.daily_video_views is not None,\
        #        """This function must be run after scraping the channel's video assets
        #        using .get_daily_video_views and updating the table in Redshift using
        #        .append_daily_video_views."""
        #assert self.dvv_appended, \
        #        """This function must be run after scraping the channel's video assets
        #        using .get_daily_video_views and updating the table in Redshift using
        #        .append_daily_video_views."""

        # Ensure Redshift table is protected from stupidity
        if test == True:
            print("\nTesting append_dvv_derivatives: \nTo turn off test mode, set test=False.\n")
            top10alltime  = 'daily_top10_videos_alltime_test'
            top10recent   = 'daily_top10_videos_recent_test'
            cvrecent = 'daily_channel_views_recent_test'
            cvalltime = 'daily_channel_views_alltime_test'
            tbl = 'daily_video_views_test'
        else:
            print("append_dvv_derivatives: This is not a test!")
            top10alltime  = 'daily_top10_videos_alltime'
            top10recent   = 'daily_top10_videos_recent'
            cvrecent = 'daily_channel_views_recent'
            cvalltime = 'daily_channel_views_alltime'
            tbl = 'daily_video_views'

        # Date
        if as_on_date is None:
            as_on_date = self.as_on_date
            if as_on_date is None:
                as_on_date = str(datetime.now()).split()[0]

        # Queries
        dates = qry("""
            SELECT view_date+1 AS as_on_date
            FROM your_schema."""+top10alltime+"""
              WHERE channel_id='"""+self.channel_id+"""'
            GROUP BY as_on_date
            """, self.con).as_on_date.astype(str)
        create_alltime = """
            DROP TABLE IF EXISTS #alltime;
            CREATE TABLE #alltime AS
              SELECT channel_id,
                video_id,
                MAX(video_name) AS video_name,
                MAX(as_on_date)-1 AS view_date,
                COALESCE(SUM(CASE WHEN as_on_date='"""+as_on_date+"""'::date THEN views END),0)
                  - COALESCE(SUM(CASE WHEN as_on_date='"""+as_on_date+"""'::date-1 THEN views END),0)
                  AS views,
                MAX(days_since_release) AS days_since_release,
                MAX(CASE WHEN as_on_date='"""+as_on_date+"""' THEN dsr_num||' '||dsr_unit END)
                  AS video_lifetime
              FROM your_schema."""+tbl+"""
                WHERE as_on_date IN ('"""+as_on_date+"""'::date, '"""+as_on_date+"""'::date-1)
                  AND channel_id = '"""+self.channel_id+"""'
              GROUP BY channel_id, video_id
            """
        create_recent = """
            DROP TABLE IF EXISTS #recent;
            CREATE TABLE #recent AS
              SELECT * FROM (
                SELECT channel_id,
                  video_id,
                  MAX(video_name) AS video_name,
                  MAX(as_on_date)-1 AS view_date,
                  COALESCE(SUM(CASE WHEN as_on_date='"""+as_on_date+"""'::date THEN views END),0)
                    - COALESCE(SUM(CASE WHEN as_on_date='"""+as_on_date+"""'::date-1 THEN views END),0)
                    AS views,
                  MAX(days_since_release) AS days_since_release,
                  MAX(CASE WHEN as_on_date='"""+as_on_date+"""' THEN dsr_num||' '||dsr_unit END)
                    AS video_lifetime
                FROM your_schema."""+tbl+"""
                  WHERE as_on_date IN ('"""+as_on_date+"""'::date, '"""+as_on_date+"""'::date-1)
                    AND channel_id = '"""+self.channel_id+"""'
                GROUP BY channel_id, video_id
              ) WHERE days_since_release < 7;
            """
        create_top10_alltime = """
            INSERT INTO your_schema."""+top10alltime+"""(
              SELECT *
              FROM #alltime
              ORDER BY views DESC
              LIMIT 10
            );"""
        create_cv_alltime = """
            INSERT INTO your_schema."""+cvalltime+"""(
               SELECT channel_id,
                 view_date,
                 SUM(views) as views
               FROM #alltime
               GROUP BY channel_id, view_date
            );"""
        create_top10_recent = """
            INSERT INTO your_schema."""+top10recent+"""(
              SELECT *
              FROM #recent
              ORDER BY views DESC
              LIMIT 10
            );"""
        create_cv_recent = """
            INSERT INTO your_schema."""+cvrecent+"""(
               SELECT channel_id,
                 view_date,
                 SUM(views) as views
               FROM #recent
               GROUP BY channel_id, view_date
             );"""

        # Execution
        if force == True:
            # Remove corresponding as_on_date from Redshift
            if as_on_date in dates.tolist():
                print("The view_date (day before "+str(as_on_date)+") already in "+\
                        top10alltime+" for channel ID "+self.channel_id+".")
                print("\t\tDeleting...")
                self.con.execute("""
                    DELETE FROM your_schema."""+top10alltime+"""
                    WHERE view_date='"""+as_on_date+"""'::date-1""")
            else:
                print("Force was unnecessary this time...")

            # Insert new as_on_date data into Redshift
            print("Inserting new data into "+top10alltime+\
                    " for channel ID "+self.channel_id+"...")
            self.con.execute(create_alltime)
            self.con.execute(create_top10_alltime)
            self.con.execute(create_cv_alltime)
            self.con.execute(create_recent)
            self.con.execute(create_top10_recent)
            self.con.execute(create_cv_recent)
        else:
            # Only insert as_on_date data if as_on_date not in Redshift table
            if as_on_date not in dates.tolist():
                print("Updating "+top10alltime+\
                        "with new view_date for channel ID "+self.channel_id+"...")
                self.con.execute(create_alltime)
                self.con.execute(create_top10_alltime)
                self.con.execute(create_cv_alltime)
                self.con.execute(create_recent)
                self.con.execute(create_top10_recent)
                self.con.execute(create_cv_recent)
            else:
                print("The as_on_date "+str(as_on_date)+" already in "+\
                        top10alltime+" for channel ID "+self.channel_id+".")
                print("Did you want to force? (force=True)")



    #----------------------------------------------------------------
    def get_daily_top10_videos_recent(self, as_on_date=None):
        if as_on_date is None:
            as_on_date = self.as_on_date
            if as_on_date is None:
                as_on_date = str(datetime.now()).split()[0]
        data = qry("""
            SELECT *
            FROM your_schema.daily_top10_videos_recent
              WHERE view_date='"""+as_on_date+"""'-1
                AND channel_id='"""+self.channel_id+"""'
              ORDER BY views DESC""",
            self.con)
        return data

    #----------------------------------------------------------------
    def get_daily_top10_videos_alltime(self, as_on_date=None):
        if as_on_date is None:
            as_on_date = self.as_on_date
            if as_on_date is None:
                as_on_date = str(datetime.now()).split()[0]
        data = qry("""
            SELECT *
            FROM your_schema.daily_top10_videos_alltime
              WHERE view_date='"""+as_on_date+"""'-1
                AND channel_id='"""+self.channel_id+"""'
              ORDER BY views DESC""",
            self.con)
        return data

    #----------------------------------------------------------------
    def get_daily_channel_views_recent(self, today=None):
        # Today
        if today is None:
            today = self.as_on_date
            if today is None:
                today = str(datetime.now()).split()[0]
        # Yesterday and the day before
        data1 = qry("""
          SELECT *
          FROM your_schema.daily_channel_views_recent
            WHERE view_date in ('"""+today+"'-1,'"+today+"""'-2)
              AND channel_id = '"""+self.channel_id+"""'
          ORDER BY view_date DESC""",
          self.con, parse_dates=['view_date'])
        # 28 More Days!
        data2 = qry("""
          SELECT channel_name as channel_id,
            view_date,
            SUM(views) AS views
          FROM your_schema.highlevel_detail_table
            WHERE debut_date + 7 > view_date
              AND view_date > '"""+today+"""' - 30
              AND LOWER(channel_name)='"""+self.channel_name.lower()+"""'
            GROUP BY view_date, channel_name
            ORDER BY view_date DESC;""",
            self.con, parse_dates=['view_date'])
        data2.channel_id = self.channel_id
        data = pd.concat([data1,data2]).reset_index(drop=True)
        TODAY = datetime.strptime(today,'%Y-%m-%d')
        start7 = TODAY-timedelta(days=7)
        start30 = TODAY-timedelta(days=30)
        end_prior = TODAY-timedelta(days=1)
        data0 = data.views[0]
        data7 =  data.loc[(data.view_date >= start7)  & (data.view_date <= end_prior)].mean()[0]
        data30 = data.loc[(data.view_date >= start30) & (data.view_date <= end_prior)].mean()[0]
        vs7dayAvg  = round(100*(data0 - data7)/data7)
        vs30dayAvg = round(100*(data0 - data30)/data7)

        return data0, vs7dayAvg, vs30dayAvg

    #----------------------------------------------------------------
    def get_daily_channel_views_alltime(self, today=None):
        # Today
        if today is None:
            today = self.as_on_date
            if today is None:
                today = str(datetime.now()).split()[0]
        # Yesterday and the day before
        data1 = qry("""
          SELECT *
          FROM your_schema.daily_channel_views_alltime
            WHERE view_date in ('"""+today+"'-1,'"+today+"""'-2)
              AND channel_id = '"""+self.channel_id+"""'
          ORDER BY view_date DESC""",
          self.con, parse_dates=['view_date'])
        # 28 More Days!
        data2 = qry("""
          SELECT channel_name as channel_id,
            view_date,
            SUM(views) AS views
          FROM your_schema.highlevel_detail_table
            WHERE view_date > '"""+today+"""' - 30
              AND LOWER(channel_name)='"""+self.channel_name.lower()+"""'
            GROUP BY view_date, channel_name
            ORDER BY view_date DESC;""",
            self.con, parse_dates=['view_date'])
        data2.channel_id = self.channel_id
        data = pd.concat([data1,data2]).reset_index(drop=True)
        TODAY = datetime.strptime(today,'%Y-%m-%d')
        start7 = TODAY-timedelta(days=7)
        start30 = TODAY-timedelta(days=30)
        end_prior = TODAY-timedelta(days=1)
        data0 = data.views[0]
        data7 =  data.loc[(data.view_date >= start7)  & (data.view_date <= end_prior)].mean()[0]
        data30 = data.loc[(data.view_date >= start30) & (data.view_date <= end_prior)].mean()[0]
        vs7dayAvg  = round(100*(data0 - data7)/data7)
        vs30dayAvg = round(100*(data0 - data30)/data7)

        return data0, vs7dayAvg, vs30dayAvg







    #def channel_daily_top_10_recent(self, scrape_data):
    #    dfd

    #def channel_daily_top_10_overall

    #def channel_daily_total_views

    #---------------------------------------------------------------------
    def channels(self, scrape_data):
        channels = scrape_data[['channel_name','channel_id','channel_url']]
        return channels.drop_duplicates()
    def append_channels(self, scrape_data):
        # Scrape Channels 
        scraped_channels = self.channels(scrape_data)
        # Get Old Data (from Redshift)
        redshift_channels  = qry("SELECT * FROM your_schema.youtube_channels", self.con)
        # Keep only new, unique rows
        channels = scraped_channels.merge(redshift_channels, indicator=True, how='left')
        channels = channels[channels._merge=='left_only']
        channels = channels.drop('_merge', axis=1)
        # Append
        if len(channels) > 0:
            print('----  UPDATING youtube_channels...  ----------------')
            for item in channels.iterrows(): print('\t'+item[1]['channel_name'])
            print('---------------------------------------------------------')
            self.redshift_append(channels, 'youtube_channels')

    #---------------------------------------------------------------------
    def list2chan(self, scrape_data):
        list2chan = scrape_data[['list_name','list_id','list_url','channel_id']]
        return list2chan.drop_duplicates()
    def append_list2chan(self, scrape_data):
        # Scrape Lists
        scraped_list2chan = self.list2chan(scrape_data)
        # Get Old Data (from Redshift)
        redshift_list2chan = qry("SELECT * FROM your_schema.playlist_channel_map", self.con)
        # Keep only new, unique rows
        list2chan = scraped_list2chan.merge(redshift_list2chan, indicator=True, how='left')
        list2chan = list2chan[list2chan._merge=='left_only']
        list2chan = list2chan.drop('_merge',axis=1)
        # Append
        if len(list2chan) > 0:
            print('----  UPDATING playlist_channel_map... ----------------')
            for item in list2chan.iterrows():
                print('\t'+item[1]['channel_id'])
                print('\t\t'+item[1]['list_name'])
            print('---------------------------------------------------------')
            self.redshift_append(list2chan, 'playlist_channel_map')

    #---------------------------------------------------------------------
    def vid2list(self, scrape_data, views=True):
        vid2list = scrape_data[['video_name','video_id','video_url','list_id']]
        return vid2list.drop_duplicates()
    def append_vid2list(self, scrape_data):
        # Scrape Videos
        scraped_vid2list = self.vid2list(scrape_data)
        # Get Old Data (from Redshift)
        redshift_vid2list  = qry("SELECT * FROM your_schema.video_playlist_map", self.con)
        # Keep only new, unique rows
        vid2list  = scraped_vid2list.merge(redshift_vid2list, indicator=True, how='left')
        vid2list  = vid2list[vid2list._merge=='left_only']
        vid2list = vid2list.drop('_merge', axis=1)
        # Append
        if len(vid2list) > 0:
            print('----  UPDATING video_playlist_map...  ----------------')
            for item in vid2list.iterrows():
                print('\tList Id: '+item[1]['list_id'])
                print('\t\tVideo: '+item[1]['video_name'])
            print('---------------------------------------------------------')
            self.redshift_append(vid2list, 'video_playlist_map')