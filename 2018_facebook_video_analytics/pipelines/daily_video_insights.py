"""
Written by Kevin Urban (2018)
"""
import pandas as pd
import re
from datetime import datetime, timedelta

"""
-------------------------------------------------------------
TO USE .metric() OR NOT TO USE .metric()
-------------------------------------------------------------
For other page and post insights, one MUST explicitly specify which metrics
to return in the request's response. However, this is not the case for video
insights.  For video insights, if no metrics are explicitly specified, then all
are returned by default (even one that cannot be explicitly specified; see note on
total_video_play_count below). This seems great until you realize how unstable
it is: With each new version of the Graph API, Facebook is prone to adding and/or
removing/renaming various metrics for video insights (or any of their insights
edges).  I've personally witnessed this in their recent upgrade to v3.0 from
v2.12.  If your code implicitly expects a certain number of metrics, or specific
metric names, etc, then this could break your code.

It seems that v3.0 changes the game a bit. While you have the option of not specifying
any metrics in version v2.12 (which returns all metrics), this does not appear to be
a stable feature in version v3.0. By "stable," I mean that the default sometimes works
as it did in v2.12, and other times throws an error.

Specifically, in version v3.0 of the Graph API, when using the Graph Explorer
(found @ developers.facebook.com/tools/explorer), I found that the video insights
edge is made to conform better with other insights edges (e.g., page and post
insights) in that one MUST explicitly specify the metric. To test whether this was
a new restriction in version v3.0, I first switched back to v2.12 and confirmed
that I could still get all video insights returned by default.  However, things got
murkier when I tested these things with a different user account. That account is
still able to grab all video insights at once when using v3.0.

I first wondered if this was a permissions thing, but I don't think it is.
I checked the permissions for both accounts, and both have: administer,
edit_profile, create_content, moderate_content, create_ads, and basic_admin
permissions.

After some light googling, I found that similar inconsistencies had occurred in
the past where different accounts could do something on the Graph API, while other
accounts couldn't.  The usual hack was to stick to using an older version (e.g.,
v2.12 vs v3.0) where the desired behavior was known to be stable.  For this project,
since (i) I cannot be sure how the service account will interact with the Graph API,
and (ii) I want this code to be as stable as possible, I will not use the older
version of the Graph API (v2.12). Instead, I will use the latest version (v3.0) and
will assume the service account behaves like a restricted account (returns an error
if no metrics are explicitly specified to the video_insights edge).

There are some implications, e.g., we might not be able to collect the
total_video_play_count metric (read more on this below).


-------------------------------------------------------------
AUTOPLAYED vs AUTO_PLAYED
-------------------------------------------------------------
underscoring of "autoplayed" is not consistent in metric
names on Facebook Graph, e.g., total_video_views_autoplayed VS
total_video_complete_views_auto_played.


-------------------------------------------------------------
TOTAL VIDEO PLAY COUNT
-------------------------------------------------------------
It seems that total_video_play_count is basically a "streams" metric, as it
is often 3-4x total_video_views, which are 3-second+ streams.

For some reason, this metric cannot be explicitly returned:
if you list this metric like "fields=video_insights.metric(total_video_play_count)",
you will receive an error message stating that it is not a valid metric. However,
total_video_play_count can be obtained if one just hits the video_insights edge
explicitly without specifying any metrics (default behavior in v2.12 is to return all
video insights when no metrics are specified; however, this is not strictly true
in v3.0).

Curiously, total_video_play_count is also not included in Facebook's
official documentation for video insights.

Since I have chosen to explicitly call on metric in this project due to the
instability of the default return-all behavior in Graph API v3.0, we
will not be collecting this metric.


-------------------------------------------------------------
MALE AND FEMALE GENDERED RETENTION GRAPHS
-------------------------------------------------------------
These are things that are available when not explicitly pulling as well.


-------------------------------------------------------------
TIME: NOTE THE INCONSISTENCIES!
-------------------------------------------------------------
In these scripts, I do not convert the time to a standard unit, but instead
leave it as Facebook provides so that the online documentation matches.  With
this in mind, take warning: time is sometimes provided in milliseconds (e.g.,
location of an ad break), seconds (e.g., the video length), or even minutes
(e.g., in time by country breakdown). Don't make any assumptions about the
unit time is reported in! For example, one might think that "time by region ID"
is reported in minutes since "time by country ID" is reported in minutes: that
would be incorrect! The "time by region ID" quantity is reported in
milliseconds (I think this table corresponds to ad regions and so is consistent
with the time unit ad breaks is reported in...but again, make no assumptions!).

Some Examples:

    * ad_breaks:            milliseconds
    * time by region:       milliseconds
    * time by dist type:    milliseconds
    * age bucket & gender:  milliseconds
    * video length:         seconds
    * time by country:      minutes

-------------------------------------------------------------
VIDEO STORIES
-------------------------------------------------------------
In v3.0, all Page and Post metrics with the word "stories" in them
have been changed, replacing "stories" with "activity". However,
this is not the case for the video metric called
total_video_stories_by_action_type.  It is something I would look
out for in future versions of the Graph API though.


-------------------------------------------------------------
RETENTION GRAPHS
-------------------------------------------------------------
Currently, we do not collect the retention graphs.  This can be filled
in easily in the future. At this point in time, there is very sparse
documentation on the retention graphs.  Here is what I picked up:
    * retention graph is %views by video segment
    * almost all videos are broken down into 40 segments
    * exception: I found that very short videos (e.g., 15 seconds)
      appear to have fewer segments
"""

#-------------------------------------
# Total Video 1D View/Time Metrics
#-------------------------------------
total_video_view_and_time_metrics = [
    'total_video_views',
    'total_video_views_unique',
    'total_video_views_autoplayed',
    'total_video_views_clicked_to_play',
    'total_video_views_organic',
    'total_video_views_organic_unique',
    'total_video_views_paid',
    'total_video_views_paid_unique',
    'total_video_views_sound_on',
    'total_video_complete_views',
    'total_video_complete_views_unique',
    'total_video_complete_views_auto_played',
    'total_video_complete_views_clicked_to_play',
    'total_video_complete_views_organic',
    'total_video_complete_views_organic_unique',
    'total_video_complete_views_paid',
    'total_video_complete_views_paid_unique',
    'total_video_30s_views',
    'total_video_30s_views_unique',
    'total_video_30s_views_auto_played',
    'total_video_30s_views_clicked_to_play',
    'total_video_30s_views_organic',
    'total_video_30s_views_paid',
    'total_video_10s_views',
    'total_video_10s_views_unique',
    'total_video_10s_views_auto_played',
    'total_video_10s_views_clicked_to_play',
    'total_video_10s_views_organic',
    'total_video_10s_views_paid',
    'total_video_10s_views_sound_on',
    #'total_video_play_count', # Unavailable through .metric() / see notes
    'total_video_avg_time_watched',
    'total_video_view_total_time',
    'total_video_view_total_time_organic',
    'total_video_view_total_time_paid',
]

#------------------------------------------------------------------
# Total Video 1D Impression Metrics
#------------------------------------------------------------------
total_video_impression_metrics = [
    'total_video_impressions',
    'total_video_impressions_unique',
    'total_video_impressions_paid_unique',
    'total_video_impressions_paid',
    'total_video_impressions_organic_unique',
    'total_video_impressions_organic',
    'total_video_impressions_viral_unique',
    'total_video_impressions_viral',
    'total_video_impressions_fan_unique',
    'total_video_impressions_fan',
    'total_video_impressions_fan_paid_unique',
    'total_video_impressions_fan_paid',
]


#------------------------------------------------------------------
# Total Video Multi-Dimensional Metrics
#------------------------------------------------------------------
total_video_multi_dimensional_metrics = [
    'total_video_views_by_distribution_type',
    'total_video_view_time_by_distribution_type',
    'total_video_view_time_by_country_id',
    'total_video_view_time_by_region_id',
    'total_video_view_time_by_age_bucket_and_gender',
    'total_video_stories_by_action_type',
    'total_video_reactions_by_type_total',
]


#------------------------------------------------------------------
# Total Video Retention Graphs
#------------------------------------------------------------------
total_video_retention_graphs = [
    'total_video_retention_graph',
    'total_video_retention_graph_autoplayed',
    'total_video_retention_graph_clicked_to_play',
    # Unavailable through .metric() / see notes
    #'total_video_retention_graph_gender_male',
    #'total_video_retention_graph_gender_female',
]


#------------------------------------------------------------------
# All Metrics
#------------------------------------------------------------------
total_video_metrics = \
    total_video_view_and_time_metrics + \
    total_video_impression_metrics + \
    total_video_multi_dimensional_metrics + \
    total_video_retention_graphs


#------------------------------------------------------------------
# Video Fields
#------------------------------------------------------------------
"""
To check whether there are more fields you want, you can perform "node introspection"
on a video node:

    fields = token.get(f"{video_id}?metadata=1")['metadata']['fields']
    field_names = [item['name'] for item in fields]

At the time of this writing, below are the fields associated with a video node.

NOTE: is_reference_only is commented out b/c it causes an error on most pages:

    {'error': {'code': 100,
     'fbtrace_id': 'DiiDqa/5GR8',
     'message': '(#100) The page is not qualified to use Video Copyright API. '
     'Please verify that the page has completed Video Copyright API '
     'onboarding process.',
     'type': 'OAuthException'}}

"""

video_fields = [
    'id',
    'title',
    'description',
    'created_time',
    'updated_time',
    'length',
    'ad_breaks',
    'privacy',
    'published',
    'live_status',
    'universal_video_id',
    'backdated_time',
    'backdated_time_granularity',
    'content_tags',
    'content_category',
    'cropped_from_params',
    'cropped_from_video_id',
    'custom_labels',
    'embed_html',
    'embeddable',
    'event',
    'format',
    'from',
    'icon',
    'is_crosspost_video',
    'is_crossposting_eligible',
    'is_instagram_eligible',
    #'is_reference_only',
    'permalink_url',
    'picture',
    'place',
    'scheduled_publish_time',
    'source',
    'status',
    'trimmed_from_params',
    'trimmed_from_video_id',
]



#------------------------------------------------------------------
# Video Edges
#------------------------------------------------------------------
"""
You can actually get A LOT MORE INFO from Facebook Graph API, e.g., explore the
various edges.  Again, perform "node introspection" on a video node to see the
available edges:

    metadata = token.get(f"{video_id}?metadata=1")
    edges = list(metadata['metadata']['connections'].keys())

At time of this writing, a video node has the following edges:
"""

video_edges = [
    'auto_generated_captions',
    'captions',
    'comments',
    'crosspost_shared_pages',
    'likes',
    'reactions',
    'sharedposts',
    'sponsor_tags',
    'tags',
    'thumbnails',
    'video_insights'
]

#------------------------------------------------------------------
# Metrics we are collecting for total video view/time table
#------------------------------------------------------------------
def get_video_insights_tables(
    token,
    page_id,
    since=None,
    until=None,
    add_date=False,
    add_datetime=False,
):
    """
    token: fb_token object (see api/graph_api.py)
    page_id: the Facebook Page ID
    since: videos released/updated since (inclusive); defaults to 15 days ago
    until: videos released/updated until (inclusive); defaults to current date
    add_date: if True, adds current date column to all tables
    add_datetime: if True, adds current datetime (at end of run) to all tables;
      since value is added at end of querying and table building, it can have
      an uncertainty of several minutes, which should not be a problem since
      our primary concern is a daily cadence, and hourly perhaps in the future;
      in fact, for most purposes, just leave this False and set add_date=True.

    Written by Kevin Urban
    """

    #-------------------------------------
    # PAGE TOKEN
    #-------------------------------------
    token.change_token_by_id(page_id)

    #-------------------------------------
    # DATE RANGE
    #-------------------------------------
    today = datetime.strptime(
            datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    if until is None:
        until = today.strftime('%Y-%m-%d')
    if since is None:
        since = (today - timedelta(days=15)).strftime('%Y-%m-%d')
    # Check if since and until are in "x days ago" format
    if len(since.split('day')) > 1:
        num_days = int(since.split('day')[0])
        since = (today - timedelta(days=num_days)).strftime('%Y-%m-%d')
    if len(until.split('day')) > 1:
        num_days = int(until.split('day')[0])
        until = (today - timedelta(days=num_days)).strftime('%Y-%m-%d')
    # Create list of video publish dates over (since,until) date range
    date_range = [str(date).split(' ')[0]
            for date in pd.date_range(since, until)]

    #-------------------------------------
    # Collect Fields and Insights
    #-------------------------------------
    video_fields_copy = ['page_id', 'page_name', 'video_id'] + video_fields.copy()
    video_fields_copy.remove('id')     # renamed to video_id
    video_fields_copy.remove('format') # a bit redundant w/ embed_html

    fields_table = pd.DataFrame(columns=video_fields_copy)

    viewership_table = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id', 'length'] +
                    total_video_view_and_time_metrics)

    impressions_table = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id'] +
                    total_video_impression_metrics)

    viewership_by_dist_type_table = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id', 'length',
                'distribution_type', 'views', 'time'])

    viewership_by_country_table = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id',
                'country', 'country_id', 'time'])

    viewership_by_region_table = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id',
                'region', 'country', 'time'])

    viewership_by_age_and_gender = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id',
                'gender', 'age', 'time'])

    video_engagement_by_action_and_reaction = pd.DataFrame(
            columns=['page_id', 'page_name', 'video_id',
                'comment', 'share', 'story_like',
                'reaction_like', 'anger', 'haha', 'love', 'sorry', 'wow'])

    for date in date_range:
        qry_str = f"me?fields=id,name,videos.since({date}T00:00:00).until({date}T23:59:59){{" \
            f"id.as(video_id),{','.join(video_fields)}," \
            f"video_insights.metric({','.join(total_video_metrics)})}}"
        response = token.get(qry_str)

        # Page ID and Name
        page_id = response['id']
        page_name = response['name']

        # Page Videos
        if 'videos' in response.keys():
            videos = response['videos']['data']
            for video in videos:

                # COLLECT FIELDS/MANAGERIAL INFO
                # -- NOTE: You will find that some videos have titles, but not
                #      description, while others will have descriptions and no
                #      title.  This is probably something that should be made
                #      more consistent on the publishing side.
                #
                # -- LISTS: Some fields are returned as lists; this script simply
                #      stringifies the list and removes the bracket symbols ([,]),
                #      leaving a comma-sep'd "list" of things in one string, e.g.,
                #      see ad_breaks, content_tags, etc.
                #
                # -- OBJECTS: Some fields are returned as objects, e.g., a User or
                #      Page object. These cases are treated on an individual basis.
                #      For more info on field data types, see:
                #          developers.facebook.com/docs/graph-api/reference/video
                keys = video.keys()
                video_id = video['video_id']
                length = video['length'] if 'length' in keys else None
                new_row = {
                'page_id': page_id,
                'page_name': page_name,
                'video_id': video_id,
                'ad_breaks': re.sub('[\[\]]', '', str(video['ad_breaks'])) \
                        if 'ad_breaks' in keys else None,
                'backdated_time': video['backdated_time'][:19].replace('T', ' ') \
                        if 'backdated_time' in keys else None,
                'backdated_time_granularity': video['backdated_time_granularity'] \
                        if 'backdated_time_granularity' in keys else None,
                'content_tags': re.sub('[\[\]]', '', str(video['content_tags'])) \
                        if 'content_tags' in keys else None,
                'content_category': video['content_category'] \
                        if 'content_category' in keys else None,
                'created_time': video['created_time'][:19].replace('T', ' ') \
                        if 'created_time' in keys else None,
                'cropped_from_params': video['cropped_from_params'] \
                        if 'cropped_from_params' in keys else None,
                'cropped_from_video_id': video['cropped_from_video_id'] \
                        if 'cropped_from_video_id' in keys else None,
                'custom_labels': re.sub('[\[\]]', '', str(video['custom_labels'])) \
                        if 'custom_labels' in keys else None,
                'description': video['description'] \
                        if 'description' in keys else None,
                'embed_html': video['embed_html'] \
                        if 'embed_html' in keys else None,
                'embeddable': video['embeddable'] \
                        if 'embeddable' in keys else None,
                'event': video['event'] if 'event' in keys else None,
                'from': video['from']['id'] \
                        if 'from' in keys else None,
                'icon': video['icon'] \
                        if 'icon' in keys else None,
                'is_crosspost_video': video['is_crosspost_video'] \
                        if 'is_crosspost_video' in keys else None,
                'is_crossposting_eligible': video['is_crossposting_eligible'] \
                        if 'is_crossposting_eligible' in keys else None,
                'is_instagram_eligible': video['is_instagram_eligible'] \
                        if 'is_instagram_eligible' in keys else None,
                'is_reference_only': video['is_reference_only'] \
                        if 'is_reference_only' in keys else None,
                'length': length,
                'live_status': video['live_status'] \
                        if 'live_status' in keys else None,
                'permalink_url': video['permalink_url'] \
                        if 'permalink_url' in keys else None,
                'picture': video['picture'] \
                        if 'picture' in keys else None,
                'place': video['place'] \
                        if 'place' in keys else None,
                'privacy': video['privacy']['value'] \
                        if 'privacy' in keys else None,
                'published': video['published'] \
                        if 'published' in keys else None,
                'scheduled_publish_time': video['scheduled_publish_time'] \
                        if 'scheduled_publish_time' in keys else None,
                'source': video['source'] \
                        if 'source' in keys else None,
                'status': video['status']['video_status'] \
                        if 'status' in keys else None,
                'title': video['title'] \
                        if 'title' in keys else None,
                'trimmed_from_params': video['trimmed_from_params'] \
                        if 'trimmed_from_params' in keys else None,
                'trimmed_from_video_id': video['trimmed_from_video_id'] \
                        if 'trimmed_from_video_id' in keys else None,
                'universal_video_id': video['universal_video_id'] \
                        if 'universal_video_id' in keys else None,
                'updated_time': video['updated_time'][:19].replace('T', ' ') \
                        if 'updated_time' in keys else None,
                 }

                # BUILD VIDEO FIELDS TABLE
                fields_table = fields_table.append(new_row, ignore_index=True)

                # COLLECT VIDEO INSIGHTS
                if 'video_insights' in video.keys():
                    video_insights = video['video_insights']['data']

                    # BUILD VIDEO VIEW/TIME TABLE
                    #  -- TIME: as of v2.12 and v3.0, view time is given in
                    #       milliseconds (ms); no conversion is made in this
                    #       code (time is left in format provided by Facebook)
                    #       this is not true for all quantities, e.g., length is given
                    #       in seconds; ad_breaks are also given in milliseconds
                    new_row = {insight['name']: insight['values'][0]['value']
                            for insight in video_insights
                            if insight['name'] in total_video_view_and_time_metrics}
                    new_row['page_id'] = page_id
                    new_row['page_name'] = page_name
                    new_row['video_id'] = video_id
                    new_row['length'] = length
                    viewership_table = viewership_table.append(
                            new_row, ignore_index=True)


                    # BUILD VIDEO IMPRESSIONS TABLE
                    new_row = {insight['name']: insight['values'][0]['value']
                            for insight in video_insights
                            if insight['name'] in total_video_impression_metrics}
                    new_row['page_id'] = page_id
                    new_row['page_name'] = page_name
                    new_row['video_id'] = video_id
                    impressions_table = impressions_table.append(
                            new_row, ignore_index=True)


                    # BUILD VIEWERSHIP BY DISTRIBUTION TYPE TABLE
                    #  -- includes views-by-dist and time-by-dist metrics
                    #  -- NOTE: Facebook does not guarantee that views by distribution type
                    #       will perfectly sum up to total_video_views (something to do
                    #       with different counting approximation schemes used while
                    #       traversing the graph)
                    #  -- TIME: as of v2.12 and v3.0, view time is given in
                    #       milliseconds (ms); no conversion is made in this
                    #       code (time is left in format provided by Facebook);
                    #       this is in contrast to other quantities, e.g., length is given
                    #       in seconds
                    for insight in video_insights:
                        # Views by Dist Type
                        if insight['name'] == 'total_video_views_by_distribution_type':
                            dist_type = insight['values'][0]['value']
                            dist_views = {
                                'page_owned': dist_type['page_owned']
                                    if 'page_owned' in dist_type.keys() else None,
                                'shared': dist_type['shared']
                                    if 'shared' in dist_type.keys() else None,
                                'crossposted': dist_type['crossposted']
                                    if 'crossposted' in dist_type.keys() else None
                            }
                        # Time by Dist Type
                        if insight['name'] == 'total_video_view_time_by_distribution_type':
                            dist_type = insight['values'][0]['value']
                            dist_time = {
                                'page_owned': dist_type['page_owned']
                                    if 'page_owned' in dist_type.keys() else None,
                                'shared': dist_type['shared']
                                    if 'shared' in dist_type.keys() else None,
                                'crossposted': dist_type['crossposted']
                                    if 'crossposted' in dist_type.keys() else None
                            }
                    new_df = pd.DataFrame(columns=['distribution_type', 'views', 'time'])
                    new_df.loc[0] = ['page_owned',
                            dist_views['page_owned'], dist_time['page_owned']]
                    new_df.loc[1] = ['shared',
                        dist_views['shared'], dist_time['shared']]
                    new_df.loc[2] = ['crossposted',
                        dist_views['crossposted'], dist_time['crossposted']]
                    new_df['page_id'] = page_id
                    new_df['page_name'] = page_name
                    new_df['video_id'] = video_id
                    viewership_by_dist_type_table = \
                        viewership_by_dist_type_table.append(new_df, ignore_index=True)


                    # BUILD VIEWERSHIP BY COUNTRY ID TABLE
                    # -- NOTE 1: Facebook only provides data on top 45 countries
                    #      engaged with Facebook; a Facebook Page may have data
                    #      for all 45, none, or anywhere in between
                    # -- NOTE 2: this video insight metric is called
                    #      total_video_view_time_by_country_id; it is not listed
                    #      or discussed in Facebook's online documentation;
                    #      some of the other metrics that are not listed in the
                    #      online docs are also not returnable using the
                    #      .metric(metric_name) approach; fortunately, this
                    #      country_id metric does not have that problem
                    for insight in video_insights:
                        if insight['name'] == 'total_video_view_time_by_country_id':
                            country_data = insight['values'][0]['value']
                    new_df = pd.DataFrame(columns=['country', 'country_id', 'time'])
                    for country in country_data:
                        ctemp = re.sub('[()]', '', country).split()
                        cname = ' '.join(ctemp[:-1])
                        cid = ctemp[-1]
                        ctime = country_data[country]
                        new_row = {'country': cname, 'country_id': cid, 'time': ctime}
                        new_df = new_df.append(new_row, ignore_index=True)
                    new_df['page_id'] = page_id
                    new_df['page_name'] = page_name
                    new_df['video_id'] = video_id
                    viewership_by_country_table = \
                        viewership_by_country_table.append(new_df, ignore_index=True)


                    # BUILD VIEWERSHIP BY REGION ID TABLE
                    # -- NOTE: the online Facebook documentation is not very helpful
                    #      concerning this metric; it states that it provides data for
                    #      the top 45 regions (reported as "Region - Country") and that
                    #      time is provided in milliseconds... And that's about it!
                    for insight in video_insights:
                        if insight['name'] == 'total_video_view_time_by_region_id':
                            region_data = insight['values'][0]['value']
                    new_df = pd.DataFrame(columns=['region', 'country', 'time'])
                    for region in region_data:
                        rname, cname = region.split(' - ')
                        rtime = region_data[region]
                        new_row = {'region': rname, 'country': cname, 'time': rtime}
                        new_df = new_df.append(new_row, ignore_index=True)
                    new_df['page_id'] = page_id
                    new_df['page_name'] = page_name
                    new_df['video_id'] = video_id
                    viewership_by_region_table = \
                        viewership_by_region_table.append(new_df, ignore_index=True)


                    # BUILD VIEWERSHIP BY AGE & GENDER TABLE
                    # -- below code hedges against potential inconsistencies in
                    #    upper/lower case naming scheme over time
                    # -- code also ensures consistent schema, i.e., Facebook
                    #    only returns nonzero age/gender buckets instead of
                    #    returning them as zeros; this code ensures that each
                    #    age/gender bucket is explicitly represented in the
                    #    flattened table
                    for insight in video_insights:
                        if insight['name'] == 'total_video_view_time_by_age_bucket_and_gender':
                            ag_buckets = insight['values'][0]['value']
                    new_df = pd.DataFrame(columns=['age', 'gender', 'time'])
                    remaining_buckets = [
                        'f.13-17', 'f.18-24', 'f.25-34', 'f.35-44',
                        'f.45-54', 'f.55-64', 'f.65+',
                        'm.13-17', 'm.18-24', 'm.25-34', 'm.35-44',
                        'm.45-54', 'm.55-64', 'm.65+',
                        'u.13-17', 'u.18-24', 'u.25-34', 'u.35-44',
                        'u.45-54', 'u.55-64', 'u.65+',
                    ]
                    for bucket in ag_buckets:
                        remaining_buckets.remove(bucket.lower())
                        gender, age = bucket.split('.')
                        age = age.replace('-', 'to').replace('+', 'plus')
                        gender = gender.lower()
                        agtime = ag_buckets[bucket]
                        new_row = {'age': age, 'gender': gender, 'time': agtime}
                        new_df = new_df.append(new_row, ignore_index=True)
                    for bucket in remaining_buckets:
                        gender, age = bucket.split('.')
                        age = age.replace('-', 'to').replace('+', 'plus')
                        new_row = {'age': age, 'gender': gender, 'time': 0}
                        new_df = new_df.append(new_row, ignore_index=True)
                    new_df['page_id'] = page_id
                    new_df['page_name'] = page_name
                    new_df['video_id'] = video_id
                    viewership_by_age_and_gender = \
                        viewership_by_age_and_gender.append(new_df, ignore_index=True)


                    # VIDEO STORIES (ENGAGEMENT) BY ACTION & REACTION TYPE
                    # -- this table combines 2 metrics:
                    #      * total_video_stories_by_action_type
                    #      * total_video_reactions_by_type_total
                    # -- NOTE: In v2.12, things like shares, comments, and likes
                    #      are called "stories". In v3.0, for page and post insights,
                    #      any metric with "story" in its name was renamed by swapping
                    #      "story" with "activity", which I think is a better name,
                    #      but still wonder, "Why not just call it engagement?"
                    #      In v3.0, for video insights, the word story was kept; I'd
                    #      watch out in future releases for this to change.
                    # -- HEAD'S UP: the like count returned by the
                    #      total_video_stories_by_action_type metric differs from the
                    #      like count returned by total_video_reactions_by_action_type.
                    #      I cannot really find much in the documentation as to why,
                    #      though I've come across similar issues in the bugs pages
                    #      where Facebook responds with answers like:
                    #         * the two numbers were generated by different approximation
                    #           algorithms
                    #         * one number is deduped (only unique users), while the other
                    #           is not
                    #      For now, we include both like counts in the table... We
                    #      can figure out which is the better number later....
                    #
                    for insight in video_insights:
                        if insight['name'] == 'total_video_stories_by_action_type':
                            actions_on_video = insight['values'][0]['value']
                        if insight['name'] == 'total_video_reactions_by_type_total':
                            reactions_on_video = insight['values'][0]['value']
                    action_types = ['comment', 'like', 'share']
                    for action in action_types:
                        if action not in actions_on_video.keys():
                            actions_on_video[action] = 0
                    actions_on_video['story_like'] = actions_on_video['like']
                    actions_on_video.pop('like')
                    reaction_types = ['like', 'love', 'wow', 'anger', 'haha', 'sorry']
                    for reaction in reaction_types:
                        if reaction not in reactions_on_video.keys():
                            reactions_on_video[action] = 0
                    reactions_on_video['reaction_like'] = reactions_on_video['like']
                    reactions_on_video.pop('like')
                    new_row = {**actions_on_video, **reactions_on_video}
                    new_row['page_id'] = page_id
                    new_row['page_name'] = page_name
                    new_row['video_id'] = video_id
                    video_engagement_by_action_and_reaction = \
                            video_engagement_by_action_and_reaction. \
                                append(new_row, ignore_index=True)



    # CREATE DICT OF ALL TABLES
    table_dict = dict()
    if len(fields_table) > 0:
        table_dict['fields'] = fields_table
    if len(viewership_table) > 0:
        table_dict['viewership'] = viewership_table
    if len(impressions_table) > 0:
        table_dict['impressions'] = impressions_table
    if len(viewership_by_dist_type_table) > 0:
        table_dict['viewership_by_dist_type'] = viewership_by_dist_type_table
    if len(viewership_by_country_table) > 0:
        table_dict['viewership_by_country'] = viewership_by_country_table
    if len(viewership_by_region_table) > 0:
        table_dict['viewership_by_region'] = viewership_by_region_table
    if len(viewership_by_age_and_gender) > 0:
        table_dict['viewership_by_age_and_gender'] = viewership_by_age_and_gender
    if len(video_engagement_by_action_and_reaction) > 0:
        table_dict['video_engagement_by_action_and_reaction'] = \
            video_engagement_by_action_and_reaction

    # SHOULD WE ADD DATE OR DATETIME COLUMNS?
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if add_date:
        for key in table_dict:
            table_dict[key]['as_on_date'] = current_date
    if add_datetime:
        for key in table_dict:
            table_dict[key]['as_on_dt'] = current_dt

    # RETURN TABLES
    return table_dict
