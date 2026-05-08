from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow
from oauth2client.file import Storage
from apiclient.discovery import build
import os
import httplib2
import pandas as pd
from math import ceil
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv() 

CLIENT_SECRETS_FILE = os.getenv('CLIENT_SECRETS_FILE')
DATA_CREDENTIALS_FILE = os.getenv('DATA_CREDENTIALS_FILE')

#----------------------------------------------------------------
def connect_to_data_api(client_secrets_file=None, data_credentials_file=None):
    if client_secrets_file is None: client_secrets_file = CLIENT_SECRETS_FILE
    if data_credentials_file is None: data_credentials_file = DATA_CREDENTIALS_FILE

    DATA_SERVICE = "youtube"
    DATA_VERSION = "v3"
    DATA_SCOPE = [
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube"
            ]

    # Authentication and Authorization
    flow = flow_from_clientsecrets(client_secrets_file, scope=DATA_SCOPE,
                message="WARNING: Please configure OAuth 2.0")
    data_storage = Storage(data_credentials_file)
    data_credentials = data_storage.get()    # Returns None if the file doesn't exist
    if data_credentials is None or data_credentials.invalid:
          data_credentials = run_flow(flow, data_storage)

    # Connect to Data API
    dapi = build(DATA_SERVICE, 
        DATA_VERSION, 
        http=data_credentials.authorize(httplib2.Http())
    )

    # Return Connection
    return dapi



#----------------------------------------
# Channels
#----------------------------------------
def get_channel_name_id_map(dapi, content_owner_id, max_results=50):
    channel_info = dapi.channels().list(
            part='snippet',
            onBehalfOfContentOwner=content_owner_id,
            managedByMe=True,
            maxResults=max_results).execute()
    channels = {channel['snippet']['title']: channel['id']
            for channel in channel_info['items']}
    return channels



#----------------------------------------
# Channel Uploads (Video Metrics)
#----------------------------------------
# The code for this fcn was borrowed from the uploads playlist fcn
#   from the "full channel scrape" project... It is adapted to meet
#   the older naming and timezone conventions of the hourly scraping
#   project. Why different conventions?  No good reasons, future
#   reader.  I just got better at all this as I went.  I'd change
#   this to conform to the newer projects, but there are various
#   dashboards and reports that depend on this table.
#
# The time_uploaded variable represents YouTube's publishedAt
#   variable.  When this project began, it was dependent on a
#   pre-existing Redshift table maintained by DE with the time_uploaded
#   naming convention...  It's unfortunate b/c in many other tables,
#   it is called publishedat, published_at, or time_published.
#
# EST: This was something that Mike had requested early on.  At one
#   point we decided UT would be better, and used that for any
#   project going forward. Since there were downstream projects
#   and reports dependent on this scraping table, we just renamed
#   the variables to be as explicit as possible.
def get_channel_uploads_video_metrics(dapi, channelId):
    # Get Uploads playlistId from channels.list
    content = dapi.channels().list(id=channelId, part='contentDetails').execute()
    try:
        # Not all of our channels have content!
        uploads = content['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except:
        empty_df = pd.DataFrame(columns=['channelId', 'channel', 'videoId', 
            'title', 'publishedAt', 'scrapeDate', 'comments', 'dislikes', 
            'favorites', 'likes', 'views'])
        return empty_df

    # Get video snippets from playlistItems.list
    list_of_snippets = []
    request = dapi.playlistItems().list(part='snippet',
        playlistId=uploads,
        maxResults=50)
    response = request.execute()
    list_of_snippets += response['items']
    while request:
      request = dapi.playlistItems().list_next(request,response)
      if request:
        response = request.execute()
        list_of_snippets += response['items']

    # Get video metrics from video.list
    video_id_list = [snippet['snippet']['resourceId']['videoId']
        for snippet in list_of_snippets]
    metrics = []
    num_videos = len(video_id_list)
    num_requests = ceil(num_videos/50)
    for k in range(num_requests):
        batch = ','.join(video_id_list[k*50:(k+1)*50])
        request = dapi.videos().list(part='statistics, snippet', id=batch)
        response = request.execute()
        metrics += response['items']

    # Flatten and Extract!
    df = pd.DataFrame(columns=['channelId', 'channel', 'videoId', 'title', 
       'publishedAt', 'scrapeDate', 'comments', 'dislikes', 'favorites', 
       'likes', 'views'])
    try: 
        channel_title = metrics[0]['snippet']['channelTitle']
    except:
        # No metrics... Some of our channels have no content.
        return df # EMPTY
    scrape_date = datetime.now().strftime('%Y-%m-%d')
    num_returned_videos = len(metrics)
    for idx in range(num_returned_videos):
        video = metrics[idx]
        title = video['snippet']['title']
        video_id = video['id']
        published_at = (video['snippet']['publishedAt'].
            replace('T',' ').
            replace('.000Z',''))
        # Ensure that returned item has a statistics component
        #  -- if not, continue to next item
        try: test = video['statistics']
        except: continue
        # Ensure metric is enabled: Things like comments can be disabled,
        #   which is represented as a nonexistence of that keyword in the 
        #   API data. This can be handled using a try/except statement.
        #   Disabled metrics are represented by -1 to differentiate them
        #   from videos measuring 0 when the metric is enabled.
        try:    comments = video['statistics']['commentCount']
        except: comments = -1
        try:    dislikes =  video['statistics']['dislikeCount']
        except: dislikes = -1
        try:    likes =  video['statistics']['likeCount']
        except: likes = -1
        # These will probably be defined no matter...i.e., x >= 0
        try:    favorites =  video['statistics']['favoriteCount']
        except: favorites = -1
        # 2018-01-02: Ran into video w/ no view count...
        try:    views =  video['statistics']['viewCount']
        except: 
            views = -1

        # Append to DataFrame
        df.loc[idx] = [channelId, channel_title, video_id, title, published_at, 
                scrape_date, comments, dislikes, favorites, likes, views]

    # Return DataFrame
    return df



#----------------------------------------
# Video Metrics (2)
#----------------------------------------
# This is just a slight re-do of the bottom half of the uploads
# code above... It's useful for other things.  Should clean all
# this up one day!
def get_video_metrics(
    dapi,
    channel_id,
    video_id_list,
):
    # Get video metrics from video.list
    metrics = []
    num_videos = len(video_id_list)
    num_requests = ceil(num_videos/50)
    for k in range(num_requests):
        batch = ','.join(video_id_list[k*50:(k+1)*50])
        request = dapi.videos().list(part='statistics, snippet', id=batch)
        response = request.execute()
        if 'items' in response: metrics += response['items']
    # Flatten and Extract!
    scrapeDate = datetime.now().strftime('%Y-%m-%d')
    df = pd.DataFrame(columns=['channelId', 'channel', 'videoId', 'title', 
        'publishedAt', 'scrapeDate', 'comments', 'dislikes', 'favorites', 
        'likes', 'views'])
    try: 
        channel_title = metrics[0]['snippet']['channelTitle']
    except:
        # No metrics... Some of our channels have no content.
        return df # EMPTY
    num_returned_videos = len(metrics)
    for idx in range(num_returned_videos):
        video = metrics[idx]
        video_id = video['id']
        title, published_at = '', ''
        if 'snippet' in video: 
            if 'title' in video['snippet']: title = video['snippet']['title']
            if 'publishedAt' in video['snippet']:
                published_at = (video['snippet']['publishedAt'].
                    replace('T',' ').
                    replace('.000Z',''))
        # Ensure that returned item has a statistics component
        #  -- if not, continue to next item
        try: test = video['statistics']
        except: continue
        # Ensure metric is enabled: Things like comments can be disabled,
        #   which is represented as a nonexistence of that keyword in the 
        #   API data. This can be handled using a try/except statement.
        #   Disabled metrics are represented by -1 to differentiate them
        #   from videos measuring 0 when the metric is enabled.
        try:    comments = video['statistics']['commentCount']
        except: comments = -1
        try:    dislikes =  video['statistics']['dislikeCount']
        except: dislikes = -1
        try:    likes =  video['statistics']['likeCount']
        except: likes = -1
        # These will probably be defined no matter...i.e., x >= 0
        try:    favorites =  video['statistics']['favoriteCount']
        except: favorites = -1
        # 2018-01-02: Ran into video w/ no view count...
        try:    views =  video['statistics']['viewCount']
        except: 
            views = -1
        # Append to DataFrame
        df.loc[idx] = [channel_id, channel_title, video_id, title, published_at, 
                scrapeDate, comments, dislikes, favorites, likes, views]
    # Return DataFrame
    return df



#----------------------------------------
# Recent Videos (Search)
#----------------------------------------
def get_recent_videos_from_search(
    dapi, 
    channel_id, 
    content_owner_id,
    n_days_back=7, 
    max_results=50,
):
    start_date = datetime.now(pytz.UTC) - timedelta(days=n_days_back)
    start_date = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    list_of_snippets = []
    request = dapi.search().list(
            part = 'snippet',
            channelId = channel_id,
            type = 'video',
            publishedAfter = start_date,
            order = 'date',
            onBehalfOfContentOwner = content_owner_id,
            maxResults = max_results)
    response = request.execute()
    list_of_snippets += response['items']
    while request:
      request = dapi.search().list_next(request,response)
      if request:
        response = request.execute()
        list_of_snippets += response['items']
    video_info = pd.DataFrame(
            columns=['video_id', 'title', 'description', 'publishedAt'])
    for idx in range(len(list_of_snippets)):
        video = list_of_snippets[idx]
        video_id = video['id']['videoId']
        title = video['snippet']['title']
        description = video['snippet']['description']
        published_at = video['snippet']['publishedAt']
        video_info.loc[idx] = [video_id, title, description, published_at]
    return video_info


#----------------------------------------
# Only Keep Recent
#----------------------------------------
def discard_content_older_than_7days(video_metrics_df):
    df = video_metrics_df
    df.publishedAt = pd.to_datetime(df.publishedAt, utc=True)
    now = datetime.now(pytz.UTC)
    now_est = datetime.now(pytz.timezone('EST'))
    df = df.copy()[df.publishedAt > now - timedelta(days=9)]
    df['time_scraped_est'] = now_est.strftime('%Y-%m-%d %H:%M:00')
    output = df.copy()[['videoId','title','views','likes','dislikes',
        'time_scraped_est', 'publishedAt']]
    # Way long ago when things were murky and in chaos, it was decided
    #   that published and scrape times would be converted to EST.  This was a 
    #   bad decision, but we live with it now b/c there are reports and 
    #   dashboards that live downstream of this code.
    # WORSE: Instead of properly converting timezone from UTC to EST, I
    #   originally used a 4-hour difference, which is correct for only
    #   half the year.
    # PROPOSAL: Warn Saday and Mike of a change to UTC. (might be more
    #   trouble than it's worth)
    output['publishedAt'] = output['publishedAt'] - timedelta(4/24)
    output.columns = ['video_id', 'title', 'views', 'likes', 'dislikes', 
            'time_scraped_est', 'time_uploaded_est']
    # Also: In previous function (borrowed from our daily API hit), missing 
    #   values were set to -1.  In original hourly scraper code, these values 
    #   were set to None/NaN. So, here we convert -1 to 0.
    output.views = output.views.astype(int)
    output.likes = output.likes.astype(int)
    output.dislikes = output.dislikes.astype(int)
    output.loc[output.views == -1,'views'] = 0
    output.loc[output.likes == -1, 'likes'] = 0
    output.loc[output.dislikes == -1, 'dislikes'] = 0

    return output