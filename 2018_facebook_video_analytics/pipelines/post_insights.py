import re
import pandas as pd

post_metrics = ','.join([
    'post_stories',
    'post_storytellers',
    'post_storytellers_by_action_type',
    'post_stories_by_action_type',
    'post_story_adds',
    'post_story_adds_unique',
    'post_story_adds_by_action_type',
    'post_story_adds_by_action_type_unique',
    'post_video_complete_views_30s_autoplayed',
    'post_video_complete_views_30s_clicked_to_play',
    'post_video_complete_views_30s_organic',
    'post_video_complete_views_30s_paid',
    'post_video_complete_views_30s_unique',
    'post_interests_impressions',
    'post_interests_impressions_unique',
    'post_interests_consumptions_unique',
    'post_interests_consumptions',
    'post_interests_consumptions_by_type_unique',
    'post_interests_consumptions_by_type',
    'post_interests_action_by_type_unique',
    'post_interests_action_by_type',
    'post_impressions',
    'post_impressions_unique',
    'post_impressions_paid',
    'post_impressions_paid_unique',
    'post_impressions_fan',
    'post_impressions_fan_unique',
    'post_impressions_fan_paid',
    'post_impressions_fan_paid_unique',
    'post_impressions_organic',
    'post_impressions_organic_unique',
    'post_impressions_viral',
    'post_impressions_viral_unique',
    'post_impressions_nonviral',
    'post_impressions_nonviral_unique',
    'post_impressions_by_story_type',
    'post_impressions_by_story_type_unique',
    'post_consumptions',
    'post_consumptions_unique',
    'post_consumptions_by_type',
    'post_consumptions_by_type_unique',
    'post_engaged_users',
    'post_negative_feedback',
    'post_negative_feedback_unique',
    'post_negative_feedback_by_type',
    'post_negative_feedback_by_type_unique',
    'post_engaged_fan',
    'post_fan_reach',
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total',
    'post_reactions_by_type_total',
    'post_video_avg_time_watched',
    'post_video_complete_views_organic',
    'post_video_complete_views_organic_unique',
    'post_video_complete_views_paid',
    'post_video_complete_views_paid_unique',
    'post_video_retention_graph',
    'post_video_retention_graph_clicked_to_play',
    'post_video_retention_graph_autoplayed',
    'post_video_views_organic',
    'post_video_views_organic_unique',
    'post_video_views_paid',
    'post_video_views_paid_unique',
    'post_video_length',
    'post_video_views',
    'post_video_views_unique',
    'post_video_views_autoplayed',
    'post_video_views_clicked_to_play',
    'post_video_views_10s',
    'post_video_views_10s_autoplayed',
    'post_video_views_10s_clicked_to_play',
    'post_video_views_10s_organic',
    'post_video_views_10s_paid',
    'post_video_views_10s_sound_on',
    'post_video_views_sound_on',
    'post_video_view_time',
    'post_video_view_time_organic',
    'post_video_view_time_by_age_bucket_and_gender',
    'post_video_view_time_by_region_id',
    'post_video_view_time_by_distribution_type',
    'post_video_views_by_distribution_type',
    'post_video_view_time_by_country_id',
    'post_video_ad_break_ad_impressions',
    'post_video_ad_break_earnings',
    'post_video_ad_break_ad_cpm',
])

def get_post_insights(token, post_id):
    post_insights = token.get(
        post_id + '/insights?metric=' + post_metrics
    )
    return post_insights['data']


def flatten_into_columns(post_insights):
    lst = []; val = []
    for item in post_insights:
        test = item['values'][0]['value']
        if type(test) == type(dict()):
            lst += [item['name'] + '_' + key + '_' + item['period']
                for key in test.keys()]
            val += [value for value in test.values()]
        else:
            lst += [item['name'] + '_' + item['period']]
            val += [test]
    lst = [re.sub('[ )\+\.]', '', item) for item in lst]
    lst = [re.sub('[(-]', '_', item).lower() for item in lst]
    val = [item if item != {} else None for item in val]
    df = pd.DataFrame(columns=lst)
    df.loc[0] = val
    return df


def flatten_post_insights(token, post_id):
    post_insights = get_post_insights(token, post_id)
